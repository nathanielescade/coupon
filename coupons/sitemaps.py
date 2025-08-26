from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from .models import Coupon, Store, Category

# coupon/sitemaps.py
class CouponSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    
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
    
    # Add images to sitemap
    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        
        # Add image information
        for url in urls:
            item = url['item']
            if hasattr(item, 'images') and item.images.exists():
                url['images'] = []
                for image in item.images.all()[:5]:  # Limit to 5 images per item
                    if image.image:
                        url['images'].append({
                            'location': image.image.url,
                            'title': image.title or item.title,
                            'caption': image.caption or item.description,
                        })
        
        return urls

class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_active_stores'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get active stores with prefetch related for better performance
        items = Store.objects.filter(
            is_active=True
        ).select_related('seo').prefetch_related('images')
        
        # Cache the queryset for 6 hours
        cache.set(cache_key, items, 60 * 60 * 6)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('store_detail', kwargs={'store_slug': obj.slug})
    
    # Add images to sitemap
    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page=page, site=site, protocol=protocol)
        
        # Add image information
        for url in urls:
            item = url['item']
            if hasattr(item, 'images') and item.images.exists():
                url['images'] = []
                for image in item.images.all()[:3]:  # Limit to 3 images per store
                    if image.image:
                        url['images'].append({
                            'location': image.image.url,
                            'title': image.title or item.name,
                            'caption': image.caption or item.description,
                        })
        
        return urls

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_active_categories'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get active categories with prefetch related for better performance
        items = Category.objects.filter(
            is_active=True
        ).select_related('seo').prefetch_related('images')
        
        # Cache the queryset for 12 hours
        cache.set(cache_key, items, 60 * 60 * 12)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('category_detail', kwargs={'category_slug': obj.slug})

class StaticViewSitemap(Sitemap):
    priority = 0.6
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

class FeaturedCouponsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.95
    
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
        ).select_related('store', 'category').prefetch_related('images')
        
        # Cache the queryset for 3 hours
        cache.set(cache_key, items, 60 * 60 * 3)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'slug': obj.slug})

class ExpiringCouponsSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.85
    
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
        ).select_related('store', 'category').prefetch_related('images')
        
        # Cache the queryset for 1 hour (shorter cache for time-sensitive content)
        cache.set(cache_key, items, 60 * 60)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'slug': obj.slug})

class ImageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    
    def items(self):
        # Try to get from cache first
        cache_key = 'sitemap_images'
        cached_items = cache.get(cache_key)
        
        if cached_items is not None:
            return cached_items
            
        # Get all images with related objects
        items = CouponImage.objects.select_related('coupon', 'store', 'category')
        
        # Cache the queryset for 12 hours
        cache.set(cache_key, items, 60 * 60 * 12)
        
        return items
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        if obj.coupon:
            return reverse('coupon_detail', kwargs={'slug': obj.coupon.slug})
        elif obj.store:
            return reverse('store_detail', kwargs={'store_slug': obj.store.slug})
        elif obj.category:
            return reverse('category_detail', kwargs={'category_slug': obj.category.slug})
        return '/'