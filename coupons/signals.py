from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Coupon, Store, Category

@receiver(post_save, sender=Coupon)
@receiver(post_delete, sender=Coupon)
def invalidate_coupon_cache(sender, instance, **kwargs):
    # Invalidate homepage sections
    cache.delete('homepage_featured_coupons')
    cache.delete('homepage_expiring_soon')
    cache.delete('homepage_latest_coupons')
    cache.delete('homepage_stores')
    cache.delete('homepage_categories')
    
    # Invalidate store page
    cache.delete(f'store_detail_{instance.store.slug}')
    
    # Invalidate category page
    cache.delete(f'category_detail_{instance.category.slug}')
    
    # Invalidate coupon detail page
    cache.delete(f'coupon_detail_{instance.id}')

@receiver(post_save, sender=Store)
@receiver(post_delete, sender=Store)
def invalidate_store_cache(sender, instance, **kwargs):
    # Invalidate store detail page
    cache.delete(f'store_detail_{instance.slug}')
    
    # Invalidate homepage stores section
    cache.delete('homepage_stores')
    
    # Invalidate all stores page
    cache.delete('all_stores')

@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    # Invalidate category detail page
    cache.delete(f'category_detail_{instance.slug}')
    
    # Invalidate homepage categories section
    cache.delete('homepage_categories')
    
    # Invalidate all categories page
    cache.delete('all_categories')