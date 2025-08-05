from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q
from django.contrib import messages
import requests
from .models import Coupon, CouponProvider, Store, Category, UserCoupon, CouponUsage
from .serializers import (
    CouponSerializer, CouponCreateSerializer, CouponProviderSerializer,
    StoreSerializer, CategorySerializer, UserCouponSerializer, CouponUsageSerializer
)

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
        context['query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context

@login_required
def save_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    user_coupon, created = UserCoupon.objects.get_or_create(
        user=request.user,
        coupon=coupon
    )
    if created:
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

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})













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