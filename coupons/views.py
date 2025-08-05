# views.py (clean up imports)
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import requests
import uuid
# views.py (update the signup_view)
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from threading import Thread
from .forms import CustomUserCreationForm
from .models import UserProfile, UserCoupon, CouponUsage

from .models import (
    Coupon, CouponProvider, Store, Category, UserCoupon, 
    CouponUsage, UserProfile
)
from .serializers import (
    CouponSerializer, CouponCreateSerializer, CouponProviderSerializer,
    StoreSerializer, CategorySerializer, UserCouponSerializer, CouponUsageSerializer
)
from .forms import CustomUserCreationForm

# API ViewSets
class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['store', 'category', 'coupon_type', 'discount_type', 'is_featured', 'is_verified']
    search_fields = ['title', 'description', 'code']
    ordering_fields = ['created_at', 'expiry_date', 'discount_value', 'usage_count']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CouponCreateSerializer
        return CouponSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def save_coupon(self, request, pk=None):
        coupon = self.get_object()
        user_coupon, created = UserCoupon.objects.get_or_create(
            user=request.user,
            coupon=coupon
        )
        if created:
            return Response({'status': 'coupon saved'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'coupon already saved'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def use_coupon(self, request, pk=None):
        coupon = self.get_object()
        
        # Check if coupon is expired
        if coupon.is_expired:
            return Response({'error': 'Coupon has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if usage limit is reached
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            return Response({'error': 'Coupon usage limit reached'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Record usage
        CouponUsage.objects.create(
            coupon=coupon,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Update usage count
        coupon.usage_count += 1
        coupon.save()
        
        # Mark as used if user saved it
        UserCoupon.objects.filter(user=request.user, coupon=coupon).update(is_used=True)
        
        return Response({'status': 'coupon used', 'code': coupon.code}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_coupons(self, request):
        saved_coupons = UserCoupon.objects.filter(user=request.user)
        serializer = UserCouponSerializer(saved_coupons, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_coupons = Coupon.objects.filter(is_featured=True, is_active=True)
        serializer = CouponSerializer(featured_coupons, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        soon = timezone.now() + timezone.timedelta(days=7)
        expiring_coupons = Coupon.objects.filter(
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now(),
            is_active=True
        )
        serializer = CouponSerializer(expiring_coupons, many=True)
        return Response(serializer.data)

class CouponProviderViewSet(viewsets.ModelViewSet):
    queryset = CouponProvider.objects.all()
    serializer_class = CouponProviderSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def fetch_coupons(self, request, pk=None):
        provider = self.get_object()
        
        try:
            headers = {}
            if provider.api_key:
                headers['Authorization'] = f'Bearer {provider.api_key}'
            
            response = requests.get(provider.api_url, headers=headers)
            response.raise_for_status()
            
            coupons_data = response.json()
            created_count = 0
            
            for coupon_data in coupons_data:
                # Get or create store
                store, _ = Store.objects.get_or_create(
                    name=coupon_data.get('store_name', 'Unknown'),
                    defaults={
                        'website': coupon_data.get('store_website', ''),
                        'slug': coupon_data.get('store_slug', ''),
                    }
                )
                
                # Get or create category
                category, _ = Category.objects.get_or_create(
                    name=coupon_data.get('category_name', 'General'),
                    defaults={
                        'slug': coupon_data.get('category_slug', ''),
                    }
                )
                
                # Create coupon
                Coupon.objects.update_or_create(
                    title=coupon_data.get('title', ''),
                    defaults={
                        'description': coupon_data.get('description', ''),
                        'code': coupon_data.get('code', ''),
                        'coupon_type': coupon_data.get('coupon_type', 'CODE'),
                        'discount_type': coupon_data.get('discount_type', 'PERCENTAGE'),
                        'discount_value': coupon_data.get('discount_value'),
                        'minimum_purchase': coupon_data.get('minimum_purchase'),
                        'start_date': coupon_data.get('start_date', timezone.now()),
                        'expiry_date': coupon_data.get('expiry_date'),
                        'affiliate_link': coupon_data.get('affiliate_link', ''),
                        'store': store,
                        'category': category,
                        'provider': provider,
                        'created_by': request.user,
                    }
                )
                created_count += 1
            
            return Response({
                'status': 'success',
                'message': f'Fetched and created {created_count} coupons from {provider.name}'
            })
            
        except requests.exceptions.RequestException as e:
            return Response({
                'status': 'error',
                'message': f'Failed to fetch coupons: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']

# Frontend Views
class HomeView(ListView):
    model = Coupon
    template_name = 'home.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    # In HomeView, StoreDetailView, CategoryDetailView, and SearchView

    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting and filtering
        if sort == 'expiring':
            # Filter to only show coupons expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            coupons = coupons.filter(expiry_date__lte=soon).order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-is_featured', '-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_coupons'] = Coupon.objects.filter(
            is_active=True,
            is_featured=True,
            expiry_date__gte=timezone.now()
        )[:6]
        context['expiring_soon'] = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=timezone.now() + timezone.timedelta(days=7),
            expiry_date__gte=timezone.now()
        )[:6]
        context['stores'] = Store.objects.filter(is_active=True)[:10]
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context

class CouponDetailView(DetailView):
    model = Coupon
    template_name = 'coupon_detail.html'
    context_object_name = 'coupon'
    slug_field = 'id'
    slug_url_kwarg = 'coupon_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_saved'] = UserCoupon.objects.filter(
                user=self.request.user,
                coupon=self.object
            ).exists()
        context['related_coupons'] = Coupon.objects.filter(
            store=self.object.store,
            is_active=True,
            expiry_date__gte=timezone.now()
        ).exclude(id=self.object.id)[:4]
        return context
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Track coupon view
        try:
            analytics, created = CouponAnalytics.objects.get_or_create(coupon=obj)
            analytics.increment_views()
        except Exception:
            pass  # Silently fail if analytics tracking fails
        
        return obj

class StoreDetailView(DetailView):
    model = Store
    template_name = 'store_detail.html'
    context_object_name = 'store'
    slug_field = 'slug'
    slug_url_kwarg = 'store_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset
        coupons = Coupon.objects.filter(
            store=self.object,
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            coupons = coupons.order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-created_at')
            
        context['coupons'] = coupons
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        return context

class CategoryDetailView(DetailView):
    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset
        coupons = Coupon.objects.filter(
            category=self.object,
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            coupons = coupons.order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-created_at')
            
        context['coupons'] = coupons
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        return context

class SearchView(ListView):
    model = Coupon
    template_name = 'search.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get search query and sort parameter
        query = self.request.GET.get('q', '')
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset - only active and non-expired coupons
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply search filter if query is provided
        if query:
            # Search in title, description, code, store name, and category name
            coupons = coupons.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(code__icontains=query) |
                Q(store__name__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        # Apply sorting
        if sort == 'expiring':
            # Filter to only show coupons expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            coupons = coupons.filter(expiry_date__lte=soon).order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-is_featured', '-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        
        # Add search result count
        query = self.request.GET.get('q', '')
        if query:
            context['search_results_count'] = self.get_queryset().count()
        
        return context
    
# coupons/views.py
@login_required
def save_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    user_coupon, created = UserCoupon.objects.get_or_create(
        user=request.user,
        coupon=coupon
    )
    
    if created:
        # Update analytics
        try:
            from analytics.models import CouponAnalytics
            analytics, created = CouponAnalytics.objects.get_or_create(coupon=coupon)
            analytics.increment_saves()
        except Exception as e:
            print(f"Error updating coupon analytics: {e}")
        
        messages.success(request, f'"{coupon.title}" has been saved to your coupons!')
    else:
        messages.info(request, f'"{coupon.title}" is already in your saved coupons.')
    
    return redirect('coupon_detail', coupon_id=coupon.id)

@login_required
def use_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    # Check if coupon is expired
    if coupon.is_expired:
        messages.error(request, 'This coupon has expired.')
        return redirect('coupon_detail', coupon_id=coupon.id)
    
    # Check if usage limit is reached
    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
        messages.error(request, 'This coupon has reached its usage limit.')
        return redirect('coupon_detail', coupon_id=coupon.id)
    
    # Record usage
    CouponUsage.objects.create(
        coupon=coupon,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Update usage count
    coupon.usage_count += 1
    coupon.save()
    
    # Mark as used if user saved it
    UserCoupon.objects.filter(user=request.user, coupon=coupon).update(is_used=True)
    
    messages.success(request, f'Coupon code: {coupon.code}')
    return redirect('coupon_detail', coupon_id=coupon.id)

@login_required
def my_coupons(request):
    saved_coupons = UserCoupon.objects.filter(user=request.user)
    context = {
        'saved_coupons': saved_coupons
    }
    return render(request, 'my_coupons.html', context)

# views.py
class CouponCreateView(LoginRequiredMixin, CreateView):
    model = Coupon
    template_name = 'coupon_form.html'
    fields = [
        'title', 'description', 'code', 'coupon_type', 'discount_type',
        'discount_value', 'minimum_purchase', 'start_date', 'expiry_date',
        'is_active', 'is_featured', 'is_verified', 'usage_limit',
        'terms_and_conditions', 'affiliate_link', 'store', 'category'
    ]
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # The UUID will be automatically generated by the model
        messages.success(self.request, 'Coupon created successfully!')
        return super().form_valid(form)

class CouponUpdateView(LoginRequiredMixin, UpdateView):
    model = Coupon
    template_name = 'coupon_form.html'
    fields = [
        'title', 'description', 'code', 'coupon_type', 'discount_type',
        'discount_value', 'minimum_purchase', 'start_date', 'expiry_date',
        'is_active', 'is_featured', 'is_verified', 'usage_limit',
        'terms_and_conditions', 'affiliate_link', 'store', 'category'
    ]
    slug_field = 'id'
    slug_url_kwarg = 'coupon_id'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, 'Coupon updated successfully!')
        return super().form_valid(form)

class CouponDeleteView(LoginRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'coupon_confirm_delete.html'
    slug_field = 'id'
    slug_url_kwarg = 'coupon_id'
    success_url = reverse_lazy('home')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Coupon deleted successfully!')
        return super().delete(request, *args, **kwargs)

# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from .models import UserProfile, UserCoupon, CouponUsage




def send_email_async(subject, message, from_email, to_email, html_message=None):
    def send():
        try:
            email = EmailMultiAlternatives(subject, message, from_email, to_email)
            if html_message:
                email.attach_alternative(html_message, "text/html")
            email.send()
        except Exception as e:
            print(f"Error sending email: {str(e)}")
    
    thread = Thread(target=send)
    thread.start()




def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Get or create the user profile
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Send verification email to the user
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': str(user_profile.email_verification_token)})
            )
            
            subject = 'Verify Your Email Address'
            message = f'Hi {user.first_name},\n\nPlease verify your email address by clicking the link below:\n\n{verification_url}\n\nThanks,\nThe CouponHub Team'
            
            # Send email asynchronously
            send_email_async(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            
            # Send notification to admin asynchronously
            admin_subject = f'New User Signup: {user.username}'
            admin_message = f'A new user has signed up on CouponHub:\n\nUsername: {user.username}\nEmail: {user.email}\nName: {user.first_name} {user.last_name}\nSignup Date: {user.date_joined}\n\nPlease verify this user account.'
            
            send_email_async(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                ['nathanielescade@gmail.com']
            )
            
            messages.success(request, f'Account created for {user.username}! Please check your email to verify your account.')
            return redirect('login')  # Immediate redirect without waiting for emails
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})




def verify_email(request, token):
    try:
        user_profile = UserProfile.objects.get(email_verification_token=token)
        user_profile.is_email_verified = True
        user_profile.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
        return redirect('login')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('signup')


# views.py (add these views)
@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Get user's profile for email verification status
    user_profile = UserProfile.get_or_create_profile(user)
    
    # Get user's saved coupons
    saved_coupons = UserCoupon.objects.filter(user=user).select_related('coupon', 'coupon__store')
    
    # Get user's coupon usage history
    used_coupons = CouponUsage.objects.filter(user=user).select_related('coupon', 'coupon__store')
    
    # Calculate statistics
    total_saved = saved_coupons.count()
    total_used = used_coupons.count()
    
    context = {
        'profile_user': user,
        'user_profile': user_profile,
        'saved_coupons': saved_coupons[:10],  # Limit to 10 for display
        'used_coupons': used_coupons[:10],   # Limit to 10 for display
        'total_saved': total_saved,
        'total_used': total_used,
        'is_own_profile': user == request.user
    }
    
    return render(request, 'registration/profile.html', context)





@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user = request.user
        old_email = user.email
        
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        new_email = request.POST.get('email', '')
        
        # Check if email is being changed
        if new_email != old_email:
            # Get or create user profile
            user_profile = UserProfile.get_or_create_profile(user)
            
            # Update email and reset verification status
            user.email = new_email
            user_profile.is_email_verified = False
            user_profile.email_verification_token = uuid.uuid4()  # Generate new token
            user_profile.save()
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': str(user_profile.email_verification_token)})
            )
            
            subject = 'Verify Your New Email Address'
            message = f'Hi {user.first_name},\n\nPlease verify your new email address by clicking the link below:\n\n{verification_url}\n\nThanks,\nThe CouponHub Team'
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [new_email],
                    fail_silently=False,
                )
                messages.info(request, 'Email updated. Please check your inbox to verify your new email address.')
            except Exception as e:
                messages.error(request, f'Email updated but we could not send verification email: {str(e)}')
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'registration/edit_profile.html')



# views.py (add this view)
# views.py (add this view)
@login_required
def resend_verification_email(request):
    try:
        # Get or create user profile
        user_profile = UserProfile.get_or_create_profile(request.user)
        
        # Only resend if email is not verified
        if not user_profile.is_email_verified:
            # Generate a new token
            user_profile.email_verification_token = uuid.uuid4()
            user_profile.save()
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': str(user_profile.email_verification_token)})
            )
            
            subject = 'Verify Your Email Address'
            message = f'Hi {request.user.first_name},\n\nPlease verify your email address by clicking the link below:\n\n{verification_url}\n\nThanks,\nThe CouponHub Team'
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Verification email sent. Please check your inbox.')
            except Exception as e:
                messages.error(request, f'Could not send verification email: {str(e)}')
        else:
            messages.info(request, 'Your email is already verified.')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('profile') 

# Add these new views to your views.py file

class AllCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting and filtering
        if sort == 'expiring':
            # Filter to only show coupons expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            coupons = coupons.filter(expiry_date__lte=soon).order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-is_featured', '-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'All Coupons'
        return context

class FeaturedCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset - only featured coupons
        coupons = Coupon.objects.filter(
            is_active=True,
            is_featured=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            soon = timezone.now() + timezone.timedelta(days=7)
            coupons = coupons.filter(expiry_date__lte=soon).order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Featured Coupons'
        return context

class ExpiringCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'expiring')
        
        # Base queryset - only coupons expiring within 7 days
        soon = timezone.now() + timezone.timedelta(days=7)
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            coupons = coupons.order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'expiring')
        context['page_title'] = 'Expiring Soon Coupons'
        return context

class LatestCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            soon = timezone.now() + timezone.timedelta(days=7)
            coupons = coupons.filter(expiry_date__lte=soon).order_by('expiry_date')
        elif sort == 'popular':
            coupons = coupons.order_by('-usage_count')
        elif sort == 'discount_high':
            coupons = coupons.order_by('-discount_value')
        else:  # newest
            coupons = coupons.order_by('-created_at')
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Latest Coupons'
        return context

class AllStoresView(ListView):
    model = Store
    template_name = 'all_stores.html'
    context_object_name = 'stores'
    paginate_by = 12
    
    def get_queryset(self):
        return Store.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Stores'
        return context

class AllCategoriesView(ListView):
    model = Category
    template_name = 'all_categories.html'
    context_object_name = 'categories'
    paginate_by = 12
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Categories'
        return context


# Add this to your views.py
from django.http import JsonResponse
from django.template.loader import render_to_string

def filter_coupons_ajax(request):
    section = request.GET.get('section')
    sort = request.GET.get('sort', 'newest')
    
    if section == 'featured':
        coupons = Coupon.objects.filter(
            is_active=True,
            is_featured=True,
            expiry_date__gte=timezone.now()
        )
        default_sort = 'popular'
    elif section == 'expiring':
        soon = timezone.now() + timezone.timedelta(days=7)
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        )
        default_sort = 'expiring'
    elif section == 'latest':
        coupons = Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        )
        default_sort = 'newest'
    else:
        return JsonResponse({'error': 'Invalid section'}, status=400)
    
    # Apply sorting
    if sort == 'expiring':
        coupons = coupons.order_by('expiry_date')
    elif sort == 'popular':
        coupons = coupons.order_by('-usage_count')
    elif sort == 'discount_high':
        coupons = coupons.order_by('-discount_value')
    else:  # newest
        coupons = coupons.order_by('-created_at')
    
    # Render the coupon cards
    context = {
        'coupons': coupons,
        'small_text': section == 'latest',
        'show_expiry': True
    }
    
    html = render_to_string('coupon_list.html', context, request=request)
    
    return JsonResponse({'html': html})