from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters  # if you haven't imported it already
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import datetime
import requests
from django.core.cache import cache  # Add this import
from django.views.decorators.cache import cache_page  # Add this import
from django.utils.decorators import method_decorator  # Add this import
from .models import (
    Coupon, CouponProvider, Store, Category, 
    UserCoupon, CouponUsage, NewsletterSubscriber, 
    Newsletter, HomePageSEO, SEO
)
from .serializers import (
    CouponSerializer, CouponCreateSerializer, CouponProviderSerializer,
    StoreSerializer, CategorySerializer, UserCouponSerializer, CouponUsageSerializer
)
from .forms import NewsletterForm
from .seo_utils import (
    get_meta_title, get_meta_description, get_breadcrumbs, 
    get_structured_data, get_open_graph_data
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
# @method_decorator(cache_page(60 * 10), name='dispatch')
class HomeView(ListView):
    model = Coupon
    template_name = 'home.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Try to get from cache first
        cache_key = f'homepage_latest_coupons_{self.request.GET.get("sort", "newest")}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try to get featured coupons from cache
        featured_coupons = cache.get('homepage_featured_coupons')
        if featured_coupons is None:
            featured_coupons = Coupon.objects.filter(
                is_active=True,
                is_featured=True,
                expiry_date__gte=timezone.now()
            )[:6]
            cache.set('homepage_featured_coupons', featured_coupons, 60 * 5)  # Cache for 5 minutes
        
        # Try to get expiring soon coupons from cache
        expiring_soon = cache.get('homepage_expiring_soon')
        if expiring_soon is None:
            expiring_soon = Coupon.objects.filter(
                is_active=True,
                expiry_date__lte=timezone.now() + timezone.timedelta(days=7),
                expiry_date__gte=timezone.now()
            )[:6]
            cache.set('homepage_expiring_soon', expiring_soon, 60 * 5)  # Cache for 5 minutes
        
        # Try to get stores from cache
        stores = cache.get('homepage_stores')
        if stores is None:
            stores = Store.objects.filter(is_active=True)[:10]
            cache.set('homepage_stores', stores, 60 * 15)  # Cache for 15 minutes
        
        # Try to get categories from cache
        categories = cache.get('homepage_categories')
        if categories is None:
            categories = Category.objects.filter(is_active=True)
            cache.set('homepage_categories', categories, 60 * 15)  # Cache for 15 minutes
        
        context['featured_coupons'] = featured_coupons
        context['expiring_soon'] = expiring_soon
        context['stores'] = stores
        context['categories'] = categories
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        
        # Get homepage SEO data
        try:
            homepage_seo = HomePageSEO.objects.get()
            context['meta_title'] = homepage_seo.meta_title
            context['meta_description'] = homepage_seo.meta_description
            context['meta_keywords'] = homepage_seo.meta_keywords
            context['hero_title'] = homepage_seo.hero_title
            context['hero_description'] = homepage_seo.hero_description
        except HomePageSEO.DoesNotExist:
            # Default values if no homepage SEO is set
            context['meta_title'] = "CouPradise - Save Money with Exclusive Coupons"
            context['meta_description'] = "Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise."
            context['meta_keywords'] = "coupons, promo codes, deals, discounts, savings, coupon codes"
            context['hero_title'] = "Save Money with Exclusive Coupons"
            context['hero_description'] = "Discover the best deals and discounts from your favorite stores."
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class CouponDetailView(DetailView):
    model = Coupon
    template_name = 'coupon_detail.html'
    context_object_name = 'coupon'
    slug_field = 'id'
    slug_url_kwarg = 'coupon_id'
    
    def get_object(self, queryset=None):
        # Try to get from cache first
        cache_key = f'coupon_detail_{self.kwargs["coupon_id"]}'
        cached_object = cache.get(cache_key)
        
        if cached_object is not None:
            return cached_object
            
        obj = super().get_object(queryset)
        
        # Cache the object
        cache.set(cache_key, obj, 60 * 10)  # Cache for 10 minutes
        
        # Track coupon view
        try:
            analytics, created = CouponAnalytics.objects.get_or_create(coupon=obj)
            analytics.increment_views()
        except Exception:
            pass  # Silently fail if analytics tracking fails
        
        return obj
    
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
        
        # Add SEO data
        context['meta_title'] = get_meta_title(self.object)
        context['meta_description'] = get_meta_description(self.object)
        context['meta_keywords'] = f"{self.object.store.name}, {self.object.category.name}, {self.object.title}, coupon, promo code, discount"
        context['structured_data'] = get_structured_data(self.object)
        context['open_graph_data'] = get_open_graph_data(self.object, self.request)
        context['breadcrumbs'] = get_breadcrumbs(self.object)
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class StoreDetailView(DetailView):
    model = Store
    template_name = 'store_detail.html'
    context_object_name = 'store'
    slug_field = 'slug'
    slug_url_kwarg = 'store_slug'
    
    def get_object(self, queryset=None):
        # Try to get from cache first
        cache_key = f'store_detail_{self.kwargs["store_slug"]}'
        cached_object = cache.get(cache_key)
        
        if cached_object is not None:
            return cached_object
            
        obj = super().get_object(queryset)
        
        # Cache the object
        cache.set(cache_key, obj, 60 * 10)  # Cache for 10 minutes
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get coupons from cache
        cache_key = f'store_{self.object.slug}_coupons_{sort}'
        coupons = cache.get(cache_key)
        
        if coupons is None:
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
                
            # Cache the coupons
            cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        context['coupons'] = coupons
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        
        # Add SEO data
        context['meta_title'] = get_meta_title(self.object)
        context['meta_description'] = get_meta_description(self.object)
        context['meta_keywords'] = f"{self.object.name}, coupons, promo codes, deals, discounts, savings"
        context['structured_data'] = get_structured_data(self.object)
        context['open_graph_data'] = get_open_graph_data(self.object, self.request)
        context['breadcrumbs'] = get_breadcrumbs(self.object)
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class CategoryDetailView(DetailView):
    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'category_slug'
    
    def get_object(self, queryset=None):
        # Try to get from cache first
        cache_key = f'category_detail_{self.kwargs["category_slug"]}'
        cached_object = cache.get(cache_key)
        
        if cached_object is not None:
            return cached_object
            
        obj = super().get_object(queryset)
        
        # Cache the object
        cache.set(cache_key, obj, 60 * 10)  # Cache for 10 minutes
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get coupons from cache
        cache_key = f'category_{self.object.slug}_coupons_{sort}'
        coupons = cache.get(cache_key)
        
        if coupons is None:
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
                
            # Cache the coupons
            cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        context['coupons'] = coupons
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        
        # Add SEO data
        context['meta_title'] = get_meta_title(self.object)
        context['meta_description'] = get_meta_description(self.object)
        context['meta_keywords'] = f"{self.object.name}, coupons, deals, discounts, savings, promo codes"
        context['structured_data'] = get_structured_data(self.object)
        context['open_graph_data'] = get_open_graph_data(self.object, self.request)
        context['breadcrumbs'] = get_breadcrumbs(self.object)
        
        return context

@method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
class SearchView(ListView):
    model = Coupon
    template_name = 'search.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get search query and sort parameter
        query = self.request.GET.get('q', '')
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'search_{query}_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        
        # Add search result count
        query = self.request.GET.get('q', '')
        if query:
            context['search_results_count'] = self.get_queryset().count()
        
        # Add SEO data
        context['meta_title'] = f"Search Results for '{query}' - CouPradise" if query else "Search Coupons - CouPradise"
        context['meta_description'] = f"Find the best coupons for '{query}'. Save money with our verified coupon codes and deals." if query else "Search for coupons, stores, and categories. Find the best deals and discounts."
        context['meta_keywords'] = f"{query}, coupons, deals, discounts, promo codes" if query else "coupons, deals, discounts, promo codes, search"
        
        return context

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
        'saved_coupons': saved_coupons,
        'meta_title': "My Saved Coupons - CouPradise",
        'meta_description': "View and manage your saved coupons. Never miss a deal with your personalized coupon collection.",
        'meta_keywords': "my coupons, saved coupons, personalized deals, coupon collection"
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
        # The UUID will be automatically generated by the model
        messages.success(self.request, 'Coupon created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = "Create a New Coupon - CouPradise"
        context['meta_description'] = "Create and share a new coupon with the CouPradise community. Help others save money!"
        context['meta_keywords'] = "create coupon, share coupon, submit deal, add discount code"
        return context

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = f"Update Coupon: {self.object.title} - CouPradise"
        context['meta_description'] = f"Update the details for {self.object.title} coupon."
        context['meta_keywords'] = f"update coupon, edit coupon, {self.object.title}, {self.object.store.name}"
        return context

class CouponDeleteView(LoginRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'coupon_confirm_delete.html'
    slug_field = 'id'
    slug_url_kwarg = 'coupon_id'
    success_url = reverse_lazy('home')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Coupon deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = f"Delete Coupon: {self.object.title} - CouPradise"
        context['meta_description'] = f"Confirm deletion of {self.object.title} coupon."
        context['meta_keywords'] = f"delete coupon, remove coupon, {self.object.title}, {self.object.store.name}"
        return context



def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
        else:
            # Form is invalid, errors will be displayed in the template
            pass
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'meta_title': "Sign Up - CouPradise",
        'meta_description': "Create a new CouPradise account to save and manage your favorite coupons.",
        'meta_keywords': "sign up, register, create account, coupon account"
    }
    return render(request, 'registration/signup.html', context)


@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(CustomUser, username=username)
    else:
        user = request.user
    
    # Get user's saved coupons
    saved_coupons = UserCoupon.objects.filter(user=user).select_related('coupon', 'coupon__store')
    
    # Get user's coupon usage history
    used_coupons = CouponUsage.objects.filter(user=user).select_related('coupon', 'coupon__store')
    
    # Calculate statistics
    total_saved = saved_coupons.count()
    total_used = used_coupons.count()
    
    context = {
        'profile_user': user,
        'saved_coupons': saved_coupons[:10],  # Limit to 10 for display
        'used_coupons': used_coupons[:10],   # Limit to 10 for display
        'total_saved': total_saved,
        'total_used': total_used,
        'is_own_profile': user == request.user,
        'meta_title': f"{user.username}'s Profile - CouPradise",
        'meta_description': f"View {user.username}'s profile, saved coupons, and usage history on CouPradise.",
        'meta_keywords': f"{user.username}, profile, saved coupons, coupon history"
    }
    
    return render(request, 'registration/profile.html', context)

# Add these new views to your views.py file
@method_decorator(cache_page(60 * 10), name='dispatch')  
class AllCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'all_coupons_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'All Coupons'
        
        # Add SEO data
        context['meta_title'] = "All Coupons - CouPradise"
        context['meta_description'] = "Browse all available coupons and deals. Save money with our verified coupon codes and discounts."
        context['meta_keywords'] = "all coupons, browse coupons, coupon codes, deals, discounts"
        
        return context

@method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
class FeaturedCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'featured_coupons_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Featured Coupons'
        
        # Add SEO data
        context['meta_title'] = "Featured Coupons - CouPradise"
        context['meta_description'] = "Discover our hand-picked featured coupons and deals. Save big with these exclusive offers."
        context['meta_keywords'] = "featured coupons, best deals, exclusive offers, hand-picked deals"
        
        return context

@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache for 5 minutes (shorter for expiring coupons)
class ExpiringCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'expiring')
        
        # Try to get from cache first
        cache_key = f'expiring_coupons_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 3)  # Cache for 3 minutes (shorter for expiring coupons)
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'expiring')
        context['page_title'] = 'Expiring Soon Coupons'
        
        # Add SEO data
        context['meta_title'] = "Expiring Soon Coupons - CouPradise"
        context['meta_description'] = "Don't miss out! These coupons are expiring soon. Use them before they're gone."
        context['meta_keywords'] = "expiring coupons, ending soon, last chance, limited time offers"
        
        return context

@method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
class LatestCouponsView(ListView):
    model = Coupon
    template_name = 'all_coupons.html'
    context_object_name = 'coupons'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'latest_coupons_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
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
            
        # Cache the queryset
        cache.set(cache_key, coupons, 60 * 5)  # Cache for 5 minutes
            
        return coupons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Latest Coupons'
        
        # Add SEO data
        context['meta_title'] = "Latest Coupons - CouPradise"
        context['meta_description'] = "Stay updated with the latest coupons and deals. Be the first to know about new offers."
        context['meta_keywords'] = "latest coupons, new deals, recent offers, fresh discounts"
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class AllStoresView(ListView):
    model = Store
    template_name = 'all_stores.html'
    context_object_name = 'stores'
    paginate_by = 12
    
    def get_queryset(self):
        # Try to get from cache first
        cache_key = 'all_stores'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        queryset = Store.objects.filter(is_active=True)
        
        # Cache the queryset
        cache.set(cache_key, queryset, 60 * 10)  # Cache for 10 minutes
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Stores'
        
        # Add SEO data
        context['meta_title'] = "All Stores - CouPradise"
        context['meta_description'] = "Browse all stores offering coupons and deals. Find discounts from your favorite brands and retailers."
        context['meta_keywords'] = "all stores, store directory, brands, retailers, shop by store"
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class AllCategoriesView(ListView):
    model = Category
    template_name = 'all_categories.html'
    context_object_name = 'categories'
    paginate_by = 12
    
    def get_queryset(self):
        # Try to get from cache first
        cache_key = 'all_categories'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        queryset = Category.objects.filter(is_active=True)
        
        # Cache the queryset
        cache.set(cache_key, queryset, 60 * 10)  # Cache for 10 minutes
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Categories'
        
        # Add SEO data
        context['meta_title'] = "All Categories - CouPradise"
        context['meta_description'] = "Browse coupons by category. Find deals for electronics, fashion, food, travel, and more."
        context['meta_keywords'] = "coupon categories, browse by category, deal categories, discount categories"
        
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

@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        
        # Check if email already exists
        if NewsletterSubscriber.objects.filter(email=email).exists():
            subscriber = NewsletterSubscriber.objects.get(email=email)
            if subscriber.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'You are already subscribed to our newsletter.'
                })
            else:
                # Reactivate subscription
                subscriber.is_active = True
                subscriber.save()
                
                # Send reactivation email
                send_subscription_email(email, "Welcome back to CouPradise!")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for re-subscribing to our newsletter!'
                })
        
        # Create new subscriber
        subscriber = form.save()
        
        # Send confirmation email
        send_subscription_email(email, "Welcome to CouPradise!")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing to our newsletter! Check your email for confirmation.'
        })
    else:
        # Return the actual form validation errors
        errors = form.errors.as_json()
        return JsonResponse({
            'success': False,
            'message': 'Please enter a valid email address.',
            'errors': errors
        }, status=400)



def send_subscription_email(email, subject):
    """Send subscription confirmation email"""
    try:
        # Render HTML email
        html_content = render_to_string('subscription_email.html', {
            'subject': subject,
            'email': email
        })
        
        # Create email message
        email_message = EmailMultiAlternatives(
            subject,
            f"Thank you for subscribing to CouPradise's newsletter!\n\nYou'll receive the latest deals and coupons directly in your inbox.",
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        
        # Attach HTML version
        email_message.attach_alternative(html_content, "text/html")
        
        # Send email
        email_message.send()
        return True
    except Exception as e:
        print(f"Error sending subscription email: {e}")
        return False

def about(request):
    context = {
        'meta_title': "About Us - CouPradise",
        'meta_description': "Learn about CouPradise's mission to help people save money with the best coupons and deals.",
        'meta_keywords': "about CouPradise, our mission, company, team"
    }
    return render(request, 'about.html', context)

def contact(request):
    context = {
        'meta_title': "Contact Us - CouPradise",
        'meta_description': "Get in touch with the CouPradise team. We'd love to hear from you!",
        'meta_keywords': "contact CouPradise, customer support, feedback, questions"
    }
    return render(request, 'contact.html', context)

def privacy_policy(request):
    context = {
        'meta_title': "Privacy Policy - CouPradise",
        'meta_description': "Read CouPradise's privacy policy to understand how we collect, use, and protect your personal information.",
        'meta_keywords': "privacy policy, data protection, personal information, GDPR"
    }
    return render(request, 'privacy_policy.html', context)

def terms_of_service(request):
    context = {
        'meta_title': "Terms of Service - CouPradise",
        'meta_description': "Read CouPradise's terms of service to understand the rules and guidelines for using our website.",
        'meta_keywords': "terms of service, terms and conditions, user agreement, website terms"
    }
    return render(request, 'terms_of_service.html', context)

@require_POST
def contact_submit(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    subject = request.POST.get('subject')
    message = request.POST.get('message')
    
    if not all([name, email, subject, message]):
        return JsonResponse({
            'success': False,
            'message': 'All fields are required.'
        })
    
    try:
        # Send email to admin
        send_mail(
            f'Contact Form: {subject}',
            f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Your message has been sent successfully. We\'ll get back to you soon!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while sending your message. Please try again.'
        })

def unsubscribe(request):
    email = request.GET.get('email')
    
    if not email:
        return render(request, 'unsubscribe.html', {
            'success': False,
            'message': 'No email provided.',
            'meta_title': "Unsubscribe - CouPradise",
            'meta_description': "Unsubscribe from CouPradise's newsletter.",
            'meta_keywords': "unsubscribe, newsletter, email preferences"
        })
    
    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        subscriber.is_active = False
        subscriber.save()
        
        return render(request, 'unsubscribe.html', {
            'success': True,
            'message': 'You have been successfully unsubscribed from our newsletter.',
            'meta_title': "Unsubscribe Successful - CouPradise",
            'meta_description': "You have been successfully unsubscribed from CouPradise's newsletter.",
            'meta_keywords': "unsubscribe successful, newsletter, email preferences"
        })
    except NewsletterSubscriber.DoesNotExist:
        return render(request, 'unsubscribe.html', {
            'success': False,
            'message': 'This email is not subscribed to our newsletter.',
            'meta_title': "Unsubscribe - CouPradise",
            'meta_description': "Unsubscribe from CouPradise's newsletter.",
            'meta_keywords': "unsubscribe, newsletter, email preferences"
        })

@staff_member_required
def newsletter_management(request):
    newsletters = Newsletter.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save()
            messages.success(request, f'Newsletter "{newsletter.subject}" created successfully!')
            return redirect('newsletter_management')
    else:
        form = NewsletterForm()
    
    context = {
        'newsletters': newsletters,
        'form': form,
        'meta_title': "Newsletter Management - CouPradise",
        'meta_description': "Manage and send newsletters to CouPradise subscribers.",
        'meta_keywords': "newsletter management, email marketing, subscriber management"
    }
    return render(request, 'newsletter_management.html', context)

@staff_member_required
def send_newsletter(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if newsletter.is_sent:
        messages.warning(request, f'Newsletter "{newsletter.subject}" was already sent on {newsletter.sent_at}')
    else:
        success, message = newsletter.send_newsletter()
        if success:
            messages.success(request, f'Newsletter sent successfully. {message}')
        else:
            messages.error(request, f'Failed to send newsletter: {message}')
    
    return redirect('newsletter_management')

@staff_member_required
def preview_newsletter(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    # Get latest coupons for the preview
    days_ago = 7
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    coupons = Coupon.objects.filter(
        is_active=True,
        created_at__gte=start_date
    ).order_by('-created_at')[:10]
    
    context = {
        'subject': newsletter.subject,
        'content': newsletter.content,
        'coupons': coupons,
        'email': 'subscriber@example.com'  # Example email for preview
    }
    
    return render(request, 'custom_newsletter_email.html', context)

def robots_txt(request):
    context = {
        'request': request
    }
    return render(request, 'robots.txt', context, content_type='text/plain')