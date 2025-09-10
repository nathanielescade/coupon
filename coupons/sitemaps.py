# coupons/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from .models import Coupon, Store, Category, Tag, User
from django.contrib.auth.models import User

class OfferSitemap(Sitemap):  
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        return Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category').order_by('-updated_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('deal_detail', kwargs={'section': obj.section, 'slug': obj.slug})

class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        cache_key = 'sitemap_active_stores'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        items = Store.objects.filter(is_active=True).order_by('name')
        cache.set(cache_key, items, 60 * 60 * 6)
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('store_detail', kwargs={'store_slug': obj.slug})

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    
    def items(self):
        cache_key = 'sitemap_active_categories'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        items = Category.objects.filter(is_active=True).order_by('name')
        cache.set(cache_key, items, 60 * 60 * 12)
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('category_detail', kwargs={'category_slug': obj.slug})

class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    
    def items(self):
        return [
            'home', 
            'all_offers', 
            'featured_offers', 
            'expiring_offers', 
            'latest_offers', 
            'all_stores', 
            'all_categories', 
            'about', 
            'contact', 
            'privacy_policy', 
            'terms_of_service'
        ]
    
    def location(self, item):
        return reverse(item)
    
    def priority(self, item):
        if item == 'home':
            return 1.0
        elif item in ['all_offers', 'featured_offers']:
            return 0.9
        elif item in ['expiring_offers', 'latest_offers', 'all_stores', 'all_categories']:
            return 0.7
        else:
            return 0.3

class FeaturedOffersSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        cache_key = 'sitemap_featured_offers'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        items = Coupon.objects.filter(
            is_active=True,
            is_featured=True,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category').order_by('-updated_at')
        cache.set(cache_key, items, 60 * 60 * 3)
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('deal_detail', kwargs={'section': obj.section, 'slug': obj.slug})

class ExpiringOffersSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.75
    
    def items(self):
        cache_key = 'sitemap_expiring_offers'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        soon = timezone.now() + timezone.timedelta(days=7)
        items = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category').order_by('expiry_date')
        cache.set(cache_key, items, 60 * 60)
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('deal_detail', kwargs={'section': obj.section, 'slug': obj.slug})

# New comprehensive sitemap classes
class DealSectionSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    
    def items(self):
        return ['coupons', 'amazon', 'special', 'deals']
    
    def location(self, section):
        return reverse('deal_section', kwargs={'section': section})
    
    def priority(self, section):
        return 0.8 if section == 'special' else 0.7

class TagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    
    def items(self):
        cache_key = 'sitemap_tags'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        items = Tag.objects.all().order_by('name')
        cache.set(cache_key, items, 60 * 60 * 24)
        return items
    
    def location(self, obj):
        return f'/tags/{obj.slug}/'

class UserSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.4
    
    def items(self):
        cache_key = 'sitemap_active_users'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        users_with_offers = User.objects.filter(
            saved_offers__isnull=False
        ).distinct().order_by('username')
        cache.set(cache_key, users_with_offers, 60 * 60 * 12)
        return users_with_offers
    
    def location(self, obj):
        return reverse('user_profile', kwargs={'username': obj.username})

class StorePageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    
    def items(self):
        cache_key = 'sitemap_store_pages'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        stores = Store.objects.filter(is_active=True).order_by('name')
        items = []
        
        for store in stores:
            offer_count = store.offers.filter(is_active=True).count()
            max_pages = min(10, (offer_count // 12) + 1)
            
            for page in range(2, max_pages + 1):
                items.append((store.slug, page))
        
        cache.set(cache_key, items, 60 * 60 * 6)
        return items
    
    def location(self, item):
        store_slug, page = item
        return f'/store/{store_slug}/?page={page}'

class CategoryPageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    
    def items(self):
        cache_key = 'sitemap_category_pages'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        categories = Category.objects.filter(is_active=True).order_by('name')
        items = []
        
        for category in categories:
            offer_count = category.offers.filter(is_active=True).count()
            max_pages = min(10, (offer_count // 12) + 1)
            
            for page in range(2, max_pages + 1):
                items.append((category.slug, page))
        
        cache.set(cache_key, items, 60 * 60 * 6)
        return items
    
    def location(self, item):
        category_slug, page = item
        return f'/category/{category_slug}/?page={page}'