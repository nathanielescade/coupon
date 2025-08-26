from django.utils.text import slugify, Truncator
from django.urls import reverse
from django.conf import settings
from .models import Coupon, Store, Category, SEO, HomePageSEO

def get_meta_title(instance, request=None):
    """Get optimized meta title for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        # First check if there's custom SEO data for this coupon
        try:
            if instance.seo and instance.seo.meta_title:
                return instance.seo.meta_title
        except SEO.DoesNotExist:
            pass
        
        # Fall back to generated title
        return f"{instance.title} - {instance.discount_display} | {instance.store.name} Coupon"
    
    elif isinstance(instance, Store):
        # First check if there's custom SEO data for this store
        try:
            if instance.seo and instance.seo.meta_title:
                return instance.seo.meta_title
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated title
        return f"{instance.name} Coupons & Promo Codes - Save Money Today"
    
    elif isinstance(instance, Category):
        # First check if there's custom SEO data for this category
        try:
            if instance.seo and instance.seo.meta_title:
                return instance.seo.meta_title
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated title
        return f"{instance.name} Coupons & Deals - Best Discounts"
    
    # Return None instead of falling back to homepage
    return None

def get_meta_description(instance, request=None):
    """Get optimized meta description for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        # First check if there's custom SEO data for this coupon
        try:
            if instance.seo and instance.seo.meta_description:
                return instance.seo.meta_description
        except SEO.DoesNotExist:
            pass
        
        # Fall back to generated description
        truncated_desc = Truncator(instance.description).words(20)
        expiry_date = instance.expiry_date.strftime('%b %d, %Y') if instance.expiry_date else 'No expiration'
        return f"Get {instance.discount_display} at {instance.store.name}. {truncated_desc} Valid until {expiry_date}."
    
    elif isinstance(instance, Store):
        # First check if there's custom SEO data for this store
        try:
            if instance.seo and instance.seo.meta_description:
                return instance.seo.meta_description
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated description
        coupon_count = instance.coupons.filter(is_active=True).count()
        return f"Find the latest {instance.name} coupons, promo codes and deals. Save money with {coupon_count} verified {instance.name} discount codes and offers."
    
    elif isinstance(instance, Category):
        # First check if there's custom SEO data for this category
        try:
            if instance.seo and instance.seo.meta_description:
                return instance.seo.meta_description
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated description
        coupon_count = instance.coupons.filter(is_active=True).count()
        return f"Browse {coupon_count} {instance.name} coupons and deals from top brands. Save money with our verified {instance.name} discount codes."
    
    # Return None instead of falling back to homepage
    return None

def get_meta_keywords(instance, request=None):
    """Get meta keywords for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        return f"{instance.store.name}, {instance.category.name}, {instance.title}, coupon, promo code, discount"
    elif isinstance(instance, Store):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        return f"{instance.name}, coupons, promo codes, deals, discounts, savings"
    elif isinstance(instance, Category):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        return f"{instance.name}, coupons, deals, discounts, savings, promo codes"
    
    # Return None instead of falling back to homepage
    return None

def get_open_graph_data(instance, request):
    """Generate Open Graph data for social sharing, using manual SEO data if available"""
    site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://coupradise.com'
    default_image = f"{site_url}/static/img/og-image.jpg"
    
    if isinstance(instance, Coupon):
        # Initialize with default values
        og_title = None
        og_description = None
        og_image = None
        twitter_title = None
        twitter_description = None
        twitter_image = None
        
        # Check if there's custom SEO data for this coupon
        try:
            if instance.seo:
                og_title = instance.seo.og_title
                og_description = instance.seo.og_description
                og_image = instance.seo.get_og_image_url  # Fixed: Removed parentheses
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                twitter_image = instance.seo.get_twitter_image_url  # Fixed: Removed parentheses
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        if not og_title:
            og_title = f"{instance.title} - {instance.discount_display}"
        
        if not og_description:
            og_description = instance.description
            
        if not og_image:
            og_image = instance.store.logo.url if instance.store.logo else default_image
            
        if not twitter_title:
            twitter_title = og_title
            
        if not twitter_description:
            twitter_description = og_description
            
        if not twitter_image:
            twitter_image = og_image
        
        return {
            'og_title': og_title,
            'og_description': og_description,
            'og_url': f"{site_url}{reverse('coupon_detail', kwargs={'coupon_id': instance.id})}",
            'og_image': og_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': twitter_title,
            'twitter_description': twitter_description,
            'twitter_image': twitter_image,
        }
    
    elif isinstance(instance, Store):
        # Similar implementation for Store
        # Initialize with default values
        og_title = None
        og_description = None
        og_image = None
        twitter_title = None
        twitter_description = None
        twitter_image = None
        
        # Check if there's custom SEO data for this store
        try:
            if instance.seo:
                og_title = instance.seo.og_title
                og_description = instance.seo.og_description
                og_image = instance.seo.get_og_image_url  # Fixed: Removed parentheses
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                twitter_image = instance.seo.get_twitter_image_url  # Fixed: Removed parentheses
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        if not og_title:
            og_title = f"{instance.name} Coupons & Promo Codes"
        
        if not og_description:
            og_description = f"Save money with {instance.name} coupons and deals"
            
        if not og_image:
            og_image = instance.logo.url if instance.logo else default_image
            
        if not twitter_title:
            twitter_title = og_title
            
        if not twitter_description:
            twitter_description = og_description
            
        if not twitter_image:
            twitter_image = og_image
        
        return {
            'og_title': og_title,
            'og_description': og_description,
            'og_url': f"{site_url}{reverse('store_detail', kwargs={'store_slug': instance.slug})}",
            'og_image': og_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': twitter_title,
            'twitter_description': twitter_description,
            'twitter_image': twitter_image,
        }
    
    elif isinstance(instance, Category):
        # Similar implementation for Category
        # Initialize with default values
        og_title = None
        og_description = None
        og_image = None
        twitter_title = None
        twitter_description = None
        twitter_image = None
        
        # Check if there's custom SEO data for this category
        try:
            if instance.seo:
                og_title = instance.seo.og_title
                og_description = instance.seo.og_description
                og_image = instance.seo.get_og_image_url  # Fixed: Removed parentheses
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                twitter_image = instance.seo.get_twitter_image_url  # Fixed: Removed parentheses
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        if not og_title:
            og_title = f"{instance.name} Coupons & Deals"
        
        if not og_description:
            og_description = f"Find the best {instance.name} coupons and deals"
            
        if not og_image:
            og_image = default_image
            
        if not twitter_title:
            twitter_title = og_title
            
        if not twitter_description:
            twitter_description = og_description
            
        if not twitter_image:
            twitter_image = og_image
        
        return {
            'og_title': og_title,
            'og_description': og_description,
            'og_url': f"{site_url}{reverse('category_detail', kwargs={'category_slug': instance.slug})}",
            'og_image': og_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': twitter_title,
            'twitter_description': twitter_description,
            'twitter_image': twitter_image,
        }
    
    # Return None instead of falling back to homepage
    return None

def get_breadcrumbs(instance):
    """Generate breadcrumb navigation for different models"""
    breadcrumbs = [{'name': 'Home', 'url': '/'}]
    
    if isinstance(instance, Coupon):
        breadcrumbs.append({'name': 'Stores', 'url': reverse('all_stores')})
        breadcrumbs.append({'name': instance.store.name, 'url': reverse('store_detail', kwargs={'store_slug': instance.store.slug})})
        breadcrumbs.append({'name': instance.title, 'url': None})
    elif isinstance(instance, Store):
        breadcrumbs.append({'name': 'Stores', 'url': reverse('all_stores')})
        breadcrumbs.append({'name': instance.name, 'url': None})
    elif isinstance(instance, Category):
        breadcrumbs.append({'name': 'Categories', 'url': reverse('all_categories')})
        breadcrumbs.append({'name': instance.name, 'url': None})
    
    return breadcrumbs

def get_structured_data(instance):
    """Generate structured data (JSON-LD) for different models"""
    if isinstance(instance, Coupon):
        return {
            "@context": "https://schema.org/",
            "@type": "Offer",
            "name": instance.title,
            "description": instance.description,
            "url": f"{settings.SITE_URL}{reverse('coupon_detail', kwargs={'coupon_id': instance.id})}",
            "availability": "https://schema.org/InStock" if instance.is_active and not instance.is_expired else "https://schema.org/OutOfStock",
            "validFrom": instance.start_date.isoformat(),
            "validThrough": instance.expiry_date.isoformat() if instance.expiry_date else None,
            "discount": instance.discount_display,
            "provider": {
                "@type": "Organization",
                "name": instance.store.name,
                "url": instance.store.website
            },
            "category": instance.category.name
        }
    elif isinstance(instance, Store):
        return {
            "@context": "https://schema.org/",
            "@type": "Store",
            "name": instance.name,
            "description": instance.description,
            "url": instance.website,
            "logo": instance.logo.url if instance.logo else None,
            "image": instance.logo.url if instance.logo else None,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "US"
            }
        }
    elif isinstance(instance, Category):
        return {
            "@context": "https://schema.org/",
            "@type": "Thing",
            "name": instance.name,
            "description": instance.description,
            "url": f"{settings.SITE_URL}{reverse('category_detail', kwargs={'category_slug': instance.slug})}"
        }
    return None