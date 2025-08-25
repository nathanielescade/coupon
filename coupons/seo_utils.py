# seo_utils.py
from django.utils.text import slugify, Truncator
from django.urls import reverse
from django.conf import settings
from .models import Coupon, Store, Category, SEO, HomePageSEO

def get_meta_title(instance, request=None):
    """Get optimized meta title for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_title:
            return instance.seo.meta_title
        return f"{instance.title} - {instance.discount_display} | {instance.store.name} Coupon"
    elif isinstance(instance, Store):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_title:
            return instance.seo.meta_title
        return f"{instance.name} Coupons & Promo Codes - Save Money Today"
    elif isinstance(instance, Category):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_title:
            return instance.seo.meta_title
        return f"{instance.name} Coupons & Deals - Best Discounts"
    
    # For homepage
    try:
        homepage_seo = HomePageSEO.objects.get()
        if homepage_seo.meta_title:
            return homepage_seo.meta_title
    except HomePageSEO.DoesNotExist:
        pass
    
    return "CouPradise - Save Money with Exclusive Coupons"

def get_meta_description(instance, request=None):
    """Get optimized meta description for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_description:
            return instance.seo.meta_description
        
        truncated_desc = Truncator(instance.description).words(20)
        expiry_date = instance.expiry_date.strftime('%b %d, %Y') if instance.expiry_date else 'No expiration'
        return f"Get {instance.discount_display} at {instance.store.name}. {truncated_desc} Valid until {expiry_date}."
    elif isinstance(instance, Store):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_description:
            return instance.seo.meta_description
        coupon_count = instance.coupons.filter(is_active=True).count()
        return f"Find the latest {instance.name} coupons, promo codes and deals. Save money with {coupon_count} verified {instance.name} discount codes and offers."
    elif isinstance(instance, Category):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_description:
            return instance.seo.meta_description
        coupon_count = instance.coupons.filter(is_active=True).count()
        return f"Browse {coupon_count} {instance.name} coupons and deals from top brands. Save money with our verified {instance.name} discount codes."
    
    # For homepage
    try:
        homepage_seo = HomePageSEO.objects.get()
        if homepage_seo.meta_description:
            return homepage_seo.meta_description
    except HomePageSEO.DoesNotExist:
        pass
    
    return "Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise."

def get_open_graph_data(instance, request):
    """Generate Open Graph data for social sharing, using manual SEO data if available"""
    site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://coupradise.com'
    default_image = f"{site_url}/static/img/og-image.jpg"
    
    if isinstance(instance, Coupon):
        og_title = None
        og_description = None
        og_image = None
        
        if hasattr(instance, 'seo') and instance.seo:
            og_title = instance.seo.og_title
            og_description = instance.seo.og_description
            og_image = instance.seo.get_og_image_url()
        
        return {
            'og_title': og_title or f"{instance.title} - {instance.discount_display}",
            'og_description': og_description or instance.description,
            'og_url': f"{site_url}{reverse('coupon_detail', kwargs={'coupon_id': instance.id})}",
            'og_image': og_image or (instance.store.logo.url if instance.store.logo else default_image),
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': (instance.seo.twitter_title if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_title else None) or og_title or f"{instance.title} - {instance.discount_display}",
            'twitter_description': (instance.seo.twitter_description if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_description else None) or og_description or instance.description,
            'twitter_image': (instance.seo.get_twitter_image_url() if hasattr(instance, 'seo') and instance.seo else None) or og_image or (instance.store.logo.url if instance.store.logo else default_image),
        }
    elif isinstance(instance, Store):
        og_title = None
        og_description = None
        og_image = None
        
        if hasattr(instance, 'seo') and instance.seo:
            og_title = instance.seo.og_title
            og_description = instance.seo.og_description
            og_image = instance.seo.get_og_image_url()
        
        return {
            'og_title': og_title or f"{instance.name} Coupons & Promo Codes",
            'og_description': og_description or f"Save money with {instance.name} coupons and deals",
            'og_url': f"{site_url}{reverse('store_detail', kwargs={'store_slug': instance.slug})}",
            'og_image': og_image or (instance.logo.url if instance.logo else default_image),
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': (instance.seo.twitter_title if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_title else None) or og_title or f"{instance.name} Coupons & Promo Codes",
            'twitter_description': (instance.seo.twitter_description if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_description else None) or og_description or f"Save money with {instance.name} coupons and deals",
            'twitter_image': (instance.seo.get_twitter_image_url() if hasattr(instance, 'seo') and instance.seo else None) or og_image or (instance.logo.url if instance.logo else default_image),
        }
    elif isinstance(instance, Category):
        og_title = None
        og_description = None
        og_image = None
        
        if hasattr(instance, 'seo') and instance.seo:
            og_title = instance.seo.og_title
            og_description = instance.seo.og_description
            og_image = instance.seo.get_og_image_url()
        
        return {
            'og_title': og_title or f"{instance.name} Coupons & Deals",
            'og_description': og_description or f"Find the best {instance.name} coupons and deals",
            'og_url': f"{site_url}{reverse('category_detail', kwargs={'category_slug': instance.slug})}",
            'og_image': og_image or default_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': (instance.seo.twitter_title if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_title else None) or og_title or f"{instance.name} Coupons & Deals",
            'twitter_description': (instance.seo.twitter_description if hasattr(instance, 'seo') and instance.seo and instance.seo.twitter_description else None) or og_description or f"Find the best {instance.name} coupons and deals",
            'twitter_image': (instance.seo.get_twitter_image_url() if hasattr(instance, 'seo') and instance.seo else None) or og_image or default_image,
        }
    
    # For homepage
    try:
        homepage_seo = HomePageSEO.objects.get()
        return {
            'og_title': homepage_seo.og_title or "CouPradise - Save Money with Exclusive Coupons",
            'og_description': homepage_seo.og_description or "Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.",
            'og_url': site_url,
            'og_image': homepage_seo.get_og_image_url() or default_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': homepage_seo.twitter_title or "CouPradise - Save Money with Exclusive Coupons",
            'twitter_description': homepage_seo.twitter_description or "Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.",
            'twitter_image': homepage_seo.get_twitter_image_url() or default_image,
        }
    except HomePageSEO.DoesNotExist:
        pass
    
    # Default Open Graph data
    return {
        'og_title': 'CouPradise - Save Money with Exclusive Coupons',
        'og_description': 'Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.',
        'og_url': f"{site_url}{request.path}",
        'og_image': default_image,
        'og_type': 'website',
        'og_site_name': 'CouPradise',
        'twitter_title': 'CouPradise - Save Money with Exclusive Coupons',
        'twitter_description': 'Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.',
        'twitter_image': default_image,
    }