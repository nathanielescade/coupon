from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from .models import Coupon, Store, Category

class CouponSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        # Only include active, non-expired coupons in sitemap
        return Coupon.objects.filter(
            is_active=True,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'slug': obj.slug})

class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_active_stores'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get active stores with prefetch related for better performance
        items = Store.objects.filter(
            is_active=True
        ).select_related('seo')
        
        # Cache the queryset for 6 hours
        cache.set(cache_key, items, 60 * 60 * 6)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('store_detail', kwargs={'store_slug': obj.slug})
    
    # Add store logo to sitemap
    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        
        # Add logo information for stores that have one
        for url in urls:
            item = url['item']
            if hasattr(item, 'logo') and item.logo:
                url['images'] = [{
                    'location': item.logo.url,
                    'title': item.name,
                    'caption': item.description or '',
                }]
        
        return urls

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_active_categories'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get active categories with prefetch related for better performance
        items = Category.objects.filter(
            is_active=True
        ).select_related('seo')
        
        # Cache the queryset for 12 hours
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
            'all_coupons', 
            'featured_coupons', 
            'expiring_coupons', 
            'latest_coupons', 
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
        # Tier 1: Homepage - Most Important
        if item == 'home':
            return 1.0
        
        # Tier 2: Main Business Pages
        elif item in ['all_coupons', 'featured_coupons']:
            return 0.9
        
        # Tier 3: Secondary Business Pages  
        elif item in ['expiring_coupons', 'latest_coupons', 'all_stores', 'all_categories']:
            return 0.7
        
        # Tier 4: Legal/Info Pages (Lower Priority)
        else:  # about, contact, privacy_policy, terms_of_service
            return 0.3

class FeaturedCouponsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_featured_coupons'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get featured coupons with prefetch related for better performance
        items = Coupon.objects.filter(
            is_active=True,
            is_featured=True,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category')
        
        # Cache the queryset for 3 hours
        cache.set(cache_key, items, 60 * 60 * 3)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'slug': obj.slug})

class ExpiringCouponsSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.75
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_expiring_coupons'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get coupons expiring within 7 days
        soon = timezone.now() + timezone.timedelta(days=7)
        items = Coupon.objects.filter(
            is_active=True,
            expiry_date__lte=soon,
            expiry_date__gte=timezone.now()
        ).select_related('store', 'category')
        
        # Cache the queryset for 1 hour (shorter cache for time-sensitive content)
        cache.set(cache_key, items, 60 * 60)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'slug': obj.slug})