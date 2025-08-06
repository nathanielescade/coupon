from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Coupon, Store, Category

class CouponSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        return Coupon.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('coupon_detail', kwargs={'coupon_id': obj.id})

class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        return Store.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('store_detail', kwargs={'store_slug': obj.slug})

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    
    def items(self):
        return Category.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('category_detail', kwargs={'category_slug': obj.slug})

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        return ['home', 'all_coupons', 'featured_coupons', 'expiring_coupons', 'latest_coupons', 'all_stores', 'all_categories', 'about', 'contact', 'privacy_policy', 'terms_of_service']
    
    def location(self, item):
        return reverse(item)