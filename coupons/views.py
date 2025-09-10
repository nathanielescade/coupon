from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.templatetags.static import static
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import datetime
import requests
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import (
    Coupon, CouponProvider, Store, Category, 
    UserOffer, OfferUsage, NewsletterSubscriber, 
    Newsletter, HomePageSEO, SEO, Tag
)
from .serializers import (
    OfferSerializer, OfferCreateSerializer, CouponProviderSerializer,
    StoreSerializer, CategorySerializer, UserOfferSerializer, OfferUsageSerializer
)
from .forms import NewsletterForm
from .seo_utils import (
    get_meta_title, get_meta_description, get_breadcrumbs, 
    get_structured_data, get_open_graph_data, get_meta_keywords
)

# API ViewSets
class OfferViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['store', 'category', 'coupon_type', 'discount_type', 'is_featured', 'is_verified', 'source', 'is_special', 'is_popular']
    search_fields = ['title', 'description', 'code']
    ordering_fields = ['created_at', 'expiry_date', 'discount_value', 'usage_count']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OfferCreateSerializer
        return OfferSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def save_offer(self, request, slug=None):
        offer = self.get_object()
        user_offer, created = UserOffer.objects.get_or_create(
            user=request.user,
            offer=offer
        )
        if created:
            return Response({'status': 'offer saved'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'offer already saved'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def use_offer(self, request, slug=None):
        offer = self.get_object()
        
        # Check if offer is expired
        if offer.is_expired:
            return Response({'error': 'Offer has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if usage limit is reached
        if offer.usage_limit and offer.usage_count >= offer.usage_limit:
            return Response({'error': 'Offer usage limit reached'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Record usage
        OfferUsage.objects.create(
            offer=offer,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Update usage count
        offer.usage_count += 1
        offer.save()
        
        # Mark as used if user saved it
        UserOffer.objects.filter(user=request.user, offer=offer).update(is_used=True)
        
        return Response({'status': 'offer used', 'code': offer.code}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_offers(self, request):
        saved_offers = UserOffer.objects.filter(user=request.user)
        serializer = UserOfferSerializer(saved_offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_offers = Coupon.objects.filter(is_featured=True, is_active=True)
        serializer = OfferSerializer(featured_offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        soon = timezone.now() + timezone.timedelta(days=7)
        expiring_offers = Coupon.objects.filter(
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now(),
            is_active=True
        )
        serializer = OfferSerializer(expiring_offers, many=True)
        return Response(serializer.data)

class CouponProviderViewSet(viewsets.ModelViewSet):
    queryset = CouponProvider.objects.all()
    serializer_class = CouponProviderSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def fetch_offers(self, request, slug=None):
        provider = self.get_object()
        
        try:
            headers = {}
            if provider.api_key:
                headers['Authorization'] = f'Bearer {provider.api_key}'
            
            response = requests.get(provider.api_url, headers=headers)
            response.raise_for_status()
            
            offers_data = response.json()
            created_count = 0
            
            for offer_data in offers_data:
                # Get or create store
                store, _ = Store.objects.get_or_create(
                    name=offer_data.get('store_name', 'Unknown'),
                    defaults={
                        'website': offer_data.get('store_website', ''),
                        'slug': offer_data.get('store_slug', ''),
                    }
                )
                
                # Get or create category
                category, _ = Category.objects.get_or_create(
                    name=offer_data.get('category_name', 'General'),
                    defaults={
                        'slug': offer_data.get('category_slug', ''),
                    }
                )
                
                # Create offer
                Coupon.objects.update_or_create(
                    title=offer_data.get('title', ''),
                    defaults={
                        'description': offer_data.get('description', ''),
                        'code': offer_data.get('code', ''),
                        'coupon_type': offer_data.get('coupon_type', 'CODE'),
                        'discount_type': offer_data.get('discount_type', 'PERCENTAGE'),
                        'discount_value': offer_data.get('discount_value'),
                        'minimum_purchase': offer_data.get('minimum_purchase'),
                        'start_date': offer_data.get('start_date', timezone.now()),
                        'expiry_date': offer_data.get('expiry_date'),
                        'affiliate_link': offer_data.get('affiliate_link', ''),
                        'store': store,
                        'category': category,
                        'provider': provider,
                        'created_by': request.user,
                    }
                )
                created_count += 1
            
            return Response({
                'status': 'success',
                'message': f'Fetched and created {created_count} offers from {provider.name}'
            })
            
        except requests.exceptions.RequestException as e:
            return Response({
                'status': 'error',
                'message': f'Failed to fetch offers: {str(e)}'
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
    context_object_name = 'offers'
    paginate_by = 12
    
    def get_queryset(self):
        # Try to get from cache first
        cache_key = f'homepage_latest_offers_{self.request.GET.get("sort", "newest")}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Base queryset - only active offers/deals
        offers = Coupon.objects.filter(is_active=True)
        
        # Apply sorting and filtering
        if sort == 'expiring':
            # Filter to only show offers expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-is_featured', '-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Try to get featured offers from cache
        featured_offers = cache.get('homepage_featured_offers')
        if featured_offers is None:
            featured_offers = Coupon.objects.filter(
                is_active=True,
                is_featured=True
            )[:6]
            cache.set('homepage_featured_offers', featured_offers, 60 * 5)  # Cache for 5 minutes
        
        # Try to get expiring soon offers from cache
        expiring_soon = cache.get('homepage_expiring_soon')
        if expiring_soon is None:
            soon = timezone.now() + timezone.timedelta(days=7)
            expiring_soon = Coupon.objects.filter(
                is_active=True,
                expiry_date__lte=soon,
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
        
        context['featured_offers'] = featured_offers
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
            
            # Handle image URLs properly
            og_image = None
            twitter_image = None
            
            if hasattr(homepage_seo, 'og_image') and homepage_seo.og_image:
                og_image = homepage_seo.og_image
            elif hasattr(homepage_seo, 'get_og_image_url') and homepage_seo.get_og_image_url:
                if callable(homepage_seo.get_og_image_url):
                    og_image = homepage_seo.get_og_image_url()
                else:
                    og_image = homepage_seo.get_og_image_url
            
            if hasattr(homepage_seo, 'twitter_image') and homepage_seo.twitter_image:
                twitter_image = homepage_seo.twitter_image
            elif hasattr(homepage_seo, 'get_twitter_image_url') and homepage_seo.get_twitter_image_url:
                if callable(homepage_seo.get_twitter_image_url):
                    twitter_image = homepage_seo.get_twitter_image_url()
                else:
                    twitter_image = homepage_seo.get_twitter_image_url
            
            # Ensure absolute URLs for social sharing
            if og_image and not og_image.startswith(('http://', 'https://')):
                og_image = self.request.build_absolute_uri(og_image)
            elif not og_image:
                try:
                    og_image = self.request.build_absolute_uri(static('img/og-image.png'))
                except:
                    og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
                
            if twitter_image and not twitter_image.startswith(('http://', 'https://')):
                twitter_image = self.request.build_absolute_uri(twitter_image)
            elif not twitter_image:
                try:
                    twitter_image = self.request.build_absolute_uri(static('img/og-image.png'))
                except:
                    twitter_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
            context['open_graph_data'] = {
                'og_title': homepage_seo.og_title,
                'og_description': homepage_seo.og_description,
                'og_image': og_image,
                'twitter_title': homepage_seo.twitter_title,
                'twitter_description': homepage_seo.twitter_description,
                'twitter_image': twitter_image,
            }
        # In the HomeView class, update the default values in the except block:

        except HomePageSEO.DoesNotExist:
            # Default values if no homepage SEO is set
            context['meta_title'] = "CouPradise - Discover Amazing Deals, Save Big Every Day"
            context['meta_description'] = "Discover the best deals and exclusive offers from your favorite stores. Save money on your online shopping with CouPradise."
            context['meta_keywords'] = "deals, offers, discounts, savings, promo codes, exclusive offers"
            context['hero_title'] = "Discover Amazing Deals, Save Big Every Day"
            context['hero_description'] = "Find the best deals and exclusive offers from top brands. Save money on every purchase with CouPradise."
            
            # Default Open Graph data with absolute URLs
            try:
                default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
            except:
                default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
                
            context['open_graph_data'] = {
                'og_title': "CouPradise - Discover Amazing Deals, Save Big Every Day",
                'og_description': "Discover the best deals and exclusive offers from your favorite stores. Save money on your online shopping with CouPradise.",
                'og_image': default_og_image,
                'twitter_title': "CouPradise - Discover Amazing Deals, Save Big Every Day",
                'twitter_description': "Discover the best deals and exclusive offers from your favorite stores. Save money on your online shopping with CouPradise.",
                'twitter_image': default_og_image,
            }
                
        return context

def deal_section(request, section):
    """View for listing deals by section"""
    # Validate section
    valid_sections = ['coupons', 'amazon', 'special', 'deals']
    if section not in valid_sections:
        raise Http404("Invalid section")
    
    # Get sort parameter
    sort = request.GET.get('sort', 'newest')
    
    # Build queryset based on section
    if section == 'coupons':
        offers = Coupon.objects.filter(
            is_active=True,
            coupon_type__in=['CODE', 'PRINTABLE', 'FREE_SHIPPING']
        )
    elif section == 'amazon':
        offers = Coupon.objects.filter(
            is_active=True,
            source='AMAZON'
        )
    elif section == 'special':
        offers = Coupon.objects.filter(
            is_active=True,
            is_special=True
        )
    elif section == 'deals':
        offers = Coupon.objects.filter(
            is_active=True,
            coupon_type='DEAL',
            is_special=False
        ).exclude(expiry_date__lt=timezone.now())
    
    # Apply sorting
    if sort == 'expiring':
        soon = timezone.now() + timezone.timedelta(days=7)
        offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
    elif sort == 'popular':
        offers = offers.order_by('-usage_count')
    elif sort == 'discount_high':
        offers = offers.order_by('-discount_value')
    else:  # newest
        offers = offers.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(offers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get section title
    section_titles = {
        'coupons': 'Coupon Codes',
        'amazon': 'Amazon Deals',
        'special': 'Special Offers',
        'deals': 'Hot Deals'
    }
    
    context = {
        'page_obj': page_obj,
        'section': section,
        'section_title': section_titles.get(section, 'Offers'),
        'current_sort': sort,
        'meta_title': f"{section_titles.get(section, 'Offers')} - CouPradise",
        'meta_description': f"Discover the best {section_titles.get(section, 'offers')} from top stores. Save money with verified offers and discounts.",
        'meta_keywords': f"{section_titles.get(section, 'offers')}, deals, discounts, savings, promo codes",
    }
    
    return render(request, 'deal_section.html', context)

def deal_detail(request, section, slug):
    """View for deal detail page"""
    # Get the offer
    offer = get_object_or_404(Coupon, slug=slug)
    
    # Check if the section matches the offer's section
    if offer.section != section:
        # Redirect to the correct section
        return redirect('deal_detail', section=offer.section, slug=slug)
    
    # Check if offer is expired
    if offer.is_expired:
        # Return 410 Gone status for expired offers
        context = {
            'offer': offer,
            'is_expired': True,
            'meta_title': f"Expired: {offer.title} - CouPradise",
            'meta_description': offer.description,
            'meta_keywords': f"expired, {offer.title}, {offer.store.name}",
        }
        response = render(request, 'offer_detail.html', context)
        response.status_code = 410  # 410 Gone tells search engines the page is permanently removed
        return response
    
    # Get related offers
    related_offers = Coupon.objects.filter(
        store=offer.store,
        is_active=True
    ).exclude(slug=slug)[:4]
    
    # Check if user has saved this offer
    is_saved = False
    if request.user.is_authenticated:
        is_saved = UserOffer.objects.filter(
            user=request.user,
            offer=offer
        ).exists()
    
    context = {
        'offer': offer,
        'related_offers': related_offers,
        'is_saved': is_saved,
        'is_expired': False,
        'meta_title': get_meta_title(offer),
        'meta_description': get_meta_description(offer),
        'meta_keywords': get_meta_keywords(offer),
        'structured_data': get_structured_data(offer),
        'breadcrumbs': get_breadcrumbs(offer),
    }
    
    # Add Open Graph data
    og_data = get_open_graph_data(offer, request)
    
    # Ensure the OG image is an absolute URL
    if 'og_image' in og_data and og_data['og_image']:
        if not og_data['og_image'].startswith(('http://', 'https://')):
            og_data['og_image'] = request.build_absolute_uri(og_data['og_image'])
    
    # Ensure the Twitter image is an absolute URL
    if 'twitter_image' in og_data and og_data['twitter_image']:
        if not og_data['twitter_image'].startswith(('http://', 'https://')):
            og_data['twitter_image'] = request.build_absolute_uri(og_data['twitter_image'])
    
    context['open_graph_data'] = og_data
    
    return render(request, 'offer_detail.html', context)



def legacy_coupon_redirect(request, slug):
    """Redirect old coupon URLs to new deal URLs"""
    offer = get_object_or_404(Coupon, slug=slug)
    return redirect(offer.get_absolute_url(), permanent=True)

@method_decorator(cache_page(60 * 15), name='dispatch')
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
        
        # Try to get offers from cache
        cache_key = f'store_{self.object.slug}_offers_{sort}'
        offers = cache.get(cache_key)
        
        if offers is None:
            # Base queryset
            offers = Coupon.objects.filter(
                store=self.object,
                is_active=True
            )
            
            # Apply sorting
            if sort == 'expiring':
                soon = timezone.now() + timezone.timedelta(days=7)
                offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
            elif sort == 'popular':
                offers = offers.order_by('-usage_count')
            elif sort == 'discount_high':
                offers = offers.order_by('-discount_value')
            else:  # newest
                offers = offers.order_by('-created_at')
                
            # Cache the offers
            cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        context['offers'] = offers
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        
        # Add SEO data
        context['meta_title'] = get_meta_title(self.object)
        context['meta_description'] = get_meta_description(self.object)
        context['meta_keywords'] = f"{self.object.name}, offers, promo codes, deals, discounts, savings"
        context['structured_data'] = get_structured_data(self.object)
        
        # Add Open Graph data with explicit image URL handling
        og_data = get_open_graph_data(self.object, self.request)
        
        # Ensure the OG image is an absolute URL
        if 'og_image' in og_data and og_data['og_image']:
            if not og_data['og_image'].startswith(('http://', 'https://')):
                og_data['og_image'] = self.request.build_absolute_uri(og_data['og_image'])
        
        # Ensure the Twitter image is an absolute URL
        if 'twitter_image' in og_data and og_data['twitter_image']:
            if not og_data['twitter_image'].startswith(('http://', 'https://')):
                og_data['twitter_image'] = self.request.build_absolute_uri(og_data['twitter_image'])
        
        context['open_graph_data'] = og_data
        context['breadcrumbs'] = get_breadcrumbs(self.object)
        
        return context

@method_decorator(cache_page(60 * 15), name='dispatch')
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
        
        # Try to get offers from cache
        cache_key = f'category_{self.object.slug}_offers_{sort}'
        offers = cache.get(cache_key)
        
        if offers is None:
            # Base queryset
            offers = Coupon.objects.filter(
                category=self.object,
                is_active=True
            )
            
            # Apply sorting
            if sort == 'expiring':
                soon = timezone.now() + timezone.timedelta(days=7)
                offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
            elif sort == 'popular':
                offers = offers.order_by('-usage_count')
            elif sort == 'discount_high':
                offers = offers.order_by('-discount_value')
            else:  # newest
                offers = offers.order_by('-created_at')
                
            # Cache the offers
            cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        context['offers'] = offers
        context['stores'] = Store.objects.filter(is_active=True)
        context['current_sort'] = sort
        
        # Add SEO data
        context['meta_title'] = get_meta_title(self.object)
        context['meta_description'] = get_meta_description(self.object)
        context['meta_keywords'] = f"{self.object.name}, offers, deals, discounts, savings, promo codes"
        context['structured_data'] = get_structured_data(self.object)
        
        # Add Open Graph data with explicit image URL handling
        og_data = get_open_graph_data(self.object, self.request)
        
        # Ensure the OG image is an absolute URL
        if 'og_image' in og_data and og_data['og_image']:
            if not og_data['og_image'].startswith(('http://', 'https://')):
                og_data['og_image'] = self.request.build_absolute_uri(og_data['og_image'])
        
        # Ensure the Twitter image is an absolute URL
        if 'twitter_image' in og_data and og_data['twitter_image']:
            if not og_data['twitter_image'].startswith(('http://', 'https://')):
                og_data['twitter_image'] = self.request.build_absolute_uri(og_data['twitter_image'])
        
        context['open_graph_data'] = og_data
        context['breadcrumbs'] = get_breadcrumbs(self.object)
        
        return context

# @method_decorator(cache_page(60 * 10), name='dispatch')
class SearchView(ListView):
    model = Coupon
    template_name = 'search.html'
    context_object_name = 'offers'
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
            
        # Base queryset - only active offers/deals
        offers = Coupon.objects.filter(is_active=True)
        
        # Apply search filter if query is provided
        if query:
            # Search in title, description, code, store name, and category name
            offers = offers.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(code__icontains=query) |
                Q(store__name__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        # Apply sorting
        if sort == 'expiring':
            # Filter to only show offers expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-is_featured', '-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        
        # Add search result count
        query = self.request.GET.get('q', '')
        if query:
            context['search_results_count'] = self.get_queryset().count()
        
        # Add SEO data
        context['meta_title'] = f"Search Results for '{query}' - CouPradise" if query else "Search Offers - CouPradise"
        context['meta_description'] = f"Find the best offers for '{query}'. Save money with our verified offers and deals." if query else "Search for offers, stores, and categories. Find the best deals and discounts."
        context['meta_keywords'] = f"{query}, offers, deals, discounts, promo codes" if query else "offers, deals, discounts, promo codes, search"
        
        return context

@login_required
def save_offer(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    user_offer, created = UserOffer.objects.get_or_create(
        user=request.user,
        offer=offer
    )
    
    if created:
        # Update analytics
        try:
            from analytics.models import OfferAnalytics
            analytics, created = OfferAnalytics.objects.get_or_create(offer=offer)
            analytics.increment_saves()
        except Exception as e:
            print(f"Error updating offer analytics: {e}")
        
        messages.success(request, f'"{offer.title}" has been saved to your offers!')
    else:
        messages.info(request, f'"{offer.title}" is already in your saved offers.')
    
    return redirect('deal_detail', section=offer.section, slug=offer.slug)

@login_required
def use_offer(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    
    # Check if offer is expired
    if offer.is_expired:
        messages.error(request, 'This offer has expired.')
        return redirect('deal_detail', section=offer.section, slug=offer.slug)
    
    # Check if usage limit is reached
    if offer.usage_limit and offer.usage_count >= offer.usage_limit:
        messages.error(request, 'This offer has reached its usage limit.')
        return redirect('deal_detail', section=offer.section, slug=offer.slug)
    
    # Record usage
    OfferUsage.objects.create(
        offer=offer,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Update usage count
    offer.usage_count += 1
    offer.save()
    
    # Mark as used if user saved it
    UserOffer.objects.filter(user=request.user, offer=offer).update(is_used=True)
    
    messages.success(request, f'Offer code: {offer.code}')
    return redirect('deal_detail', section=offer.section, slug=offer.slug)

@login_required
def my_offers(request):
    saved_offers = UserOffer.objects.filter(user=request.user)
    context = {
        'saved_offers': saved_offers,
        'meta_title': "My Saved Offers - CouPradise",
        'meta_description': "View and manage your saved offers. Never miss a deal with your personalized offer collection.",
        'meta_keywords': "my offers, saved offers, personalized deals, offer collection"
    }
    return render(request, 'my_offers.html', context)

class OfferCreateView(LoginRequiredMixin, CreateView):
    model = Coupon
    template_name = 'offer_form.html'
    fields = [
        'title', 'description', 'code', 'coupon_type', 'discount_type',
        'discount_value', 'minimum_purchase', 'start_date', 'expiry_date',
        'is_active', 'is_featured', 'is_verified', 'is_special', 'is_popular',
        'usage_limit', 'terms_and_conditions', 'affiliate_link', 'store', 'category',
        'source', 'tags'
    ]
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Offer created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = "Create a New Offer - CouPradise"
        context['meta_description'] = "Create and share a new offer with the CouPradise community. Help others save money!"
        context['meta_keywords'] = "create offer, share offer, submit deal, add discount code"
        return context

class OfferUpdateView(LoginRequiredMixin, UpdateView):
    model = Coupon
    template_name = 'offer_form.html'
    fields = [
        'title', 'description', 'code', 'coupon_type', 'discount_type',
        'discount_value', 'minimum_purchase', 'start_date', 'expiry_date',
        'is_active', 'is_featured', 'is_verified', 'is_special', 'is_popular',
        'usage_limit', 'terms_and_conditions', 'affiliate_link', 'store', 'category',
        'source', 'tags'
    ]
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, 'Offer updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = f"Update Offer: {self.object.title} - CouPradise"
        context['meta_description'] = f"Update the details for {self.object.title} offer."
        context['meta_keywords'] = f"update offer, edit offer, {self.object.title}, {self.object.store.name}"
        return context

class OfferDeleteView(LoginRequiredMixin, DeleteView):
    model = Coupon
    template_name = 'offer_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('home')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Offer deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['meta_title'] = f"Delete Offer: {self.object.title} - CouPradise"
        context['meta_description'] = f"Confirm deletion of {self.object.title} offer."
        context['meta_keywords'] = f"delete offer, remove offer, {self.object.title}, {self.object.store.name}"
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
        'meta_description': "Create a new CouPradise account to save and manage your favorite offers.",
        'meta_keywords': "sign up, register, create account, offer account"
    }
    return render(request, 'registration/signup.html', context)

@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    # Get user's saved offers
    saved_offers = UserOffer.objects.filter(user=user).select_related('offer', 'offer__store')
    
    # Get user's offer usage history
    used_offers = OfferUsage.objects.filter(user=user).select_related('offer', 'offer__store')
    
    # Calculate statistics
    total_saved = saved_offers.count()
    total_used = used_offers.count()
    
    context = {
        'profile_user': user,
        'saved_offers': saved_offers[:10],  # Limit to 10 for display
        'used_offers': used_offers[:10],   # Limit to 10 for display
        'total_saved': total_saved,
        'total_used': total_used,
        'is_own_profile': user == request.user,
        'meta_title': f"{user.username}'s Profile - CouPradise",
        'meta_description': f"View {user.username}'s profile, saved offers, and usage history on CouPradise.",
        'meta_keywords': f"{user.username}, profile, saved offers, offer history"
    }
    
    return render(request, 'registration/profile.html', context)

# Add these new views to your views.py file
# @method_decorator(cache_page(60 * 10), name='dispatch')  
class AllOffersView(ListView):
    model = Coupon
    template_name = 'all_offers.html'
    context_object_name = 'offers'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'all_offers_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        # Base queryset
        offers = Coupon.objects.filter(is_active=True)
        
        # Apply sorting and filtering
        if sort == 'expiring':
            # Filter to only show offers expiring within 7 days
            soon = timezone.now() + timezone.timedelta(days=7)
            offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-is_featured', '-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'All Offers'
        
        # Add SEO data
        context['meta_title'] = "All Offers - CouPradise"
        context['meta_description'] = "Browse all available offers and deals. Save money with our verified offers and discounts."
        context['meta_keywords'] = "all offers, browse offers, offer codes, deals, discounts"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "All Offers - CouPradise",
            'og_description': "Browse all available offers and deals. Save money with our verified offers and discounts.",
            'og_image': default_og_image,
            'twitter_title': "All Offers - CouPradise",
            'twitter_description': "Browse all available offers and deals. Save money with our verified offers and discounts.",
            'twitter_image': default_og_image,
        }
        
        return context

# @method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
class FeaturedOffersView(ListView):
    model = Coupon
    template_name = 'all_offers.html'
    context_object_name = 'offers'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'featured_offers_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        # Base queryset - only featured offers
        offers = Coupon.objects.filter(
            is_active=True,
            is_featured=True
        )
        
        # Apply sorting
        if sort == 'expiring':
            soon = timezone.now() + timezone.timedelta(days=7)
            offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Featured Offers'
        
        # Add SEO data
        context['meta_title'] = "Featured Offers - CouPradise"
        context['meta_description'] = "Discover our hand-picked featured offers and deals. Save big with these exclusive offers."
        context['meta_keywords'] = "featured offers, best deals, exclusive offers, hand-picked deals"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "Featured Offers - CouPradise",
            'og_description': "Discover our hand-picked featured offers and deals. Save big with these exclusive offers.",
            'og_image': default_og_image,
            'twitter_title': "Featured Offers - CouPradise",
            'twitter_description': "Discover our hand-picked featured offers and deals. Save big with these exclusive offers.",
            'twitter_image': default_og_image,
        }
        
        return context

@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache for 5 minutes (shorter for expiring offers)
class ExpiringOffersView(ListView):
    model = Coupon
    template_name = 'all_offers.html'
    context_object_name = 'offers'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'expiring')
        
        # Try to get from cache first
        cache_key = f'expiring_offers_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        # Base queryset - only offers expiring within 7 days
        soon = timezone.now() + timezone.timedelta(days=7)
        offers = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        )
        
        # Apply sorting
        if sort == 'expiring':
            offers = offers.order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 3)  # Cache for 3 minutes (shorter for expiring offers)
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'expiring')
        context['page_title'] = 'Expiring Soon Offers'
        
        # Add SEO data
        context['meta_title'] = "Expiring Soon Offers - CouPradise"
        context['meta_description'] = "Don't miss out! These offers are expiring soon. Use them before they're gone."
        context['meta_keywords'] = "expiring offers, ending soon, last chance, limited time offers"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "Expiring Soon Offers - CouPradise",
            'og_description': "Don't miss out! These offers are expiring soon. Use them before they're gone.",
            'og_image': default_og_image,
            'twitter_title': "Expiring Soon Offers - CouPradise",
            'twitter_description': "Don't miss out! These offers are expiring soon. Use them before they're gone.",
            'twitter_image': default_og_image,
        }
        
        return context

# @method_decorator(cache_page(60 * 10), name='dispatch')  # Cache for 10 minutes
class LatestOffersView(ListView):
    model = Coupon
    template_name = 'all_offers.html'
    context_object_name = 'offers'
    paginate_by = 12
    
    def get_queryset(self):
        # Get sort parameter
        sort = self.request.GET.get('sort', 'newest')
        
        # Try to get from cache first
        cache_key = f'latest_offers_{sort}'
        cached_queryset = cache.get(cache_key)
        
        if cached_queryset is not None:
            return cached_queryset
            
        # Base queryset
        offers = Coupon.objects.filter(is_active=True)
        
        # Apply sorting
        if sort == 'expiring':
            soon = timezone.now() + timezone.timedelta(days=7)
            offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
        elif sort == 'popular':
            offers = offers.order_by('-usage_count')
        elif sort == 'discount_high':
            offers = offers.order_by('-discount_value')
        else:  # newest
            offers = offers.order_by('-created_at')
            
        # Cache the queryset
        cache.set(cache_key, offers, 60 * 5)  # Cache for 5 minutes
            
        return offers
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['page_title'] = 'Latest Offers'
        
        # Add SEO data
        context['meta_title'] = "Latest Offers - CouPradise"
        context['meta_description'] = "Stay updated with the latest offers and deals. Be the first to know about new offers."
        context['meta_keywords'] = "latest offers, new deals, recent offers, fresh discounts"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "Latest Offers - CouPradise",
            'og_description': "Stay updated with the latest offers and deals. Be the first to know about new offers.",
            'og_image': default_og_image,
            'twitter_title': "Latest Offers - CouPradise",
            'twitter_description': "Stay updated with the latest offers and deals. Be the first to know about new offers.",
            'twitter_image': default_og_image,
        }
        
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
        context['meta_description'] = "Browse all stores offering offers and deals. Find discounts from your favorite brands and retailers."
        context['meta_keywords'] = "all stores, store directory, brands, retailers, shop by store"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "All Stores - CouPradise",
            'og_description': "Browse all stores offering offers and deals. Find discounts from your favorite brands and retailers.",
            'og_image': default_og_image,
            'twitter_title': "All Stores - CouPradise",
            'twitter_description': "Browse all stores offering offers and deals. Find discounts from your favorite brands and retailers.",
            'twitter_image': default_og_image,
        }
        
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
        context['meta_description'] = "Browse offers by category. Find deals for electronics, fashion, food, travel, and more."
        context['meta_keywords'] = "offer categories, browse by category, deal categories, discount categories"
        
        # Add Open Graph data
        try:
            default_og_image = self.request.build_absolute_uri(static('img/og-image.png'))
        except:
            default_og_image = f"{self.request.scheme}://{self.request.get_host()}/static/img/og-image.png"
            
        context['open_graph_data'] = {
            'og_title': "All Categories - CouPradise",
            'og_description': "Browse offers by category. Find deals for electronics, fashion, food, travel, and more.",
            'og_image': default_og_image,
            'twitter_title': "All Categories - CouPradise",
            'twitter_description': "Browse offers by category. Find deals for electronics, fashion, food, travel, and more.",
            'twitter_image': default_og_image,
        }
        
        return context

def filter_offers_ajax(request):
    section = request.GET.get('section')
    sort = request.GET.get('sort', 'newest')
    
    # Determine the section based on the current page
    if not section:
        # Try to determine section from the current URL
        path = request.path
        if path.startswith('/deals/'):
            parts = path.split('/')
            if len(parts) >= 3:
                section = parts[2]  # Extract section from URL like /deals/coupons/
        
        # Default to home if we can't determine the section
        if not section:
            section = 'home'
    
    if section == 'home':
        offers = Coupon.objects.filter(is_active=True)
    elif section == 'special':
        offers = Coupon.objects.filter(
            is_active=True,
            is_special=True
        )
    elif section == 'amazon':
        offers = Coupon.objects.filter(
            is_active=True,
            source='AMAZON'
        )
    elif section == 'coupons':
        offers = Coupon.objects.filter(
            is_active=True,
            coupon_type__in=['CODE', 'PRINTABLE', 'FREE_SHIPPING']
        )
    elif section == 'deals':
        offers = Coupon.objects.filter(
            is_active=True,
            coupon_type='DEAL',
            is_special=False
        ).exclude(expiry_date__lt=timezone.now())
    elif section == 'featured':
        offers = Coupon.objects.filter(
            is_active=True,
            is_featured=True
        )
    elif section == 'expiring':
        soon = timezone.now() + timezone.timedelta(days=7)
        offers = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        )
    else:
        return JsonResponse({'error': 'Invalid section'}, status=400)
    
    # Apply sorting
    if sort == 'expiring':
        soon = timezone.now() + timezone.timedelta(days=7)
        offers = offers.filter(expiry_date__lte=soon, expiry_date__gte=timezone.now()).order_by('expiry_date')
    elif sort == 'popular':
        offers = offers.order_by('-usage_count')
    elif sort == 'discount_high':
        offers = offers.order_by('-discount_value')
    else:  # newest
        offers = offers.order_by('-created_at')
    
    # Render the offer cards
    context = {
        'offers': offers,
        'small_text': True,
        'show_expiry': True
    }
    
    html = render_to_string('offer_list.html', context, request=request)
    
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
            f"Thank you for subscribing to CouPradise's newsletter!\n\nYou'll receive the latest deals and offers directly in your inbox.",
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
    # Add Open Graph data
    try:
        default_og_image = request.build_absolute_uri(static('img/og-image.png'))
    except:
        default_og_image = f"{request.scheme}://{request.get_host()}/static/img/og-image.png"
        
    context = {
        'meta_title': "About Us - CouPradise",
        'meta_description': "Learn about CouPradise's mission to help people save money with the best offers and deals.",
        'meta_keywords': "about CouPradise, our mission, company, team",
        'open_graph_data': {
            'og_title': "About Us - CouPradise",
            'og_description': "Learn about CouPradise's mission to help people save money with the best offers and deals.",
            'og_image': default_og_image,
            'twitter_title': "About Us - CouPradise",
            'twitter_description': "Learn about CouPradise's mission to help people save money with the best offers and deals.",
            'twitter_image': default_og_image,
        }
    }
    return render(request, 'about.html', context)

def contact(request):
    # Add Open Graph data
    try:
        default_og_image = request.build_absolute_uri(static('img/og-image.png'))
    except:
        default_og_image = f"{request.scheme}://{request.get_host()}/static/img/og-image.png"
        
    context = {
        'meta_title': "Contact Us - CouPradise",
        'meta_description': "Get in touch with the CouPradise team. We'd love to hear from you!",
        'meta_keywords': "contact CouPradise, customer support, feedback, questions",
        'open_graph_data': {
            'og_title': "Contact Us - CouPradise",
            'og_description': "Get in touch with the CouPradise team. We'd love to hear from you!",
            'og_image': default_og_image,
            'twitter_title': "Contact Us - CouPradise",
            'twitter_description': "Get in touch with the CouPradise team. We'd love to hear from you!",
            'twitter_image': default_og_image,
        }
    }
    return render(request, 'contact.html', context)

def privacy_policy(request):
    # Add Open Graph data
    try:
        default_og_image = request.build_absolute_uri(static('img/og-image.png'))
    except:
        default_og_image = f"{request.scheme}://{request.get_host()}/static/img/og-image.png"
        
    context = {
        'meta_title': "Privacy Policy - CouPradise",
        'meta_description': "Read CouPradise's privacy policy to understand how we collect, use, and protect your personal information.",
        'meta_keywords': "privacy policy, data protection, personal information, GDPR",
        'open_graph_data': {
            'og_title': "Privacy Policy - CouPradise",
            'og_description': "Read CouPradise's privacy policy to understand how we collect, use, and protect your personal information.",
            'og_image': default_og_image,
            'twitter_title': "Privacy Policy - CouPradise",
            'twitter_description': "Read CouPradise's privacy policy to understand how we collect, use, and protect your personal information.",
            'twitter_image': default_og_image,
        }
    }
    return render(request, 'privacy_policy.html', context)

def terms_of_service(request):
    # Add Open Graph data
    try:
        default_og_image = request.build_absolute_uri(static('img/og-image.png'))
    except:
        default_og_image = f"{request.scheme}://{request.get_host()}/static/img/og-image.png"
        
    context = {
        'meta_title': "Terms of Service - CouPradise",
        'meta_description': "Read CouPradise's terms of service to understand the rules and guidelines for using our website.",
        'meta_keywords': "terms of service, terms and conditions, user agreement, website terms",
        'open_graph_data': {
            'og_title': "Terms of Service - CouPradise",
            'og_description': "Read CouPradise's terms of service to understand the rules and guidelines for using our website.",
            'og_image': default_og_image,
            'twitter_title': "Terms of Service - CouPradise",
            'twitter_description': "Read CouPradise's terms of service to understand the rules and guidelines for using our website.",
            'twitter_image': default_og_image,
        }
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
    
    # Get latest offers for the preview
    days_ago = 7
    start_date = timezone.now() - datetime.timedelta(days=days_ago)
    offers = Coupon.objects.filter(
        is_active=True,
        created_at__gte=start_date
    ).order_by('-created_at')[:10]
    
    context = {
        'subject': newsletter.subject,
        'content': newsletter.content,
        'offers': offers,
        'email': 'subscriber@example.com'  # Example email for preview
    }
    
    return render(request, 'custom_newsletter_email.html', context)






# coupons/views.py (add this view)
def tag_detail(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    
    offers = Coupon.objects.filter(
        tags=tag,
        is_active=True
    ).order_by('-created_at')
    
    paginator = Paginator(offers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
        'meta_title': f"{tag.name} Deals & Offers - CouPradise",
        'meta_description': f"Find the best {tag.name} deals and offers. Save money with our verified {tag.name} discounts.",
        'meta_keywords': f"{tag.name}, deals, offers, discounts, promo codes",
    }
    
    return render(request, 'tag_detail.html', context)