from django.utils.text import slugify, Truncator
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils import timezone
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
        
        # Fall back to generated title with optimization
        discount_display = instance.discount_display
        store_name = instance.store.name
        category_name = instance.category.name if instance.category else ""
        
        # Create a compelling title with emotional triggers
        if category_name:
            return f"{discount_display} {category_name} Coupon at {store_name} - Limited Time Offer"
        else:
            return f"{discount_display} {store_name} Coupon - Save Money Today"
    
    elif isinstance(instance, Store):
        # First check if there's custom SEO data for this store
        try:
            if instance.seo and instance.seo.meta_title:
                return instance.seo.meta_title
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated title with optimization
        coupon_count = Coupon.objects.filter(store=instance, is_active=True).count()
        
        if coupon_count > 0:
            return f"{instance.name} Coupons: {coupon_count} Promo Codes for {timezone.now().strftime('%B %Y')}"
        else:
            return f"{instance.name} Coupons & Promo Codes - Save Money Today"
    
    elif isinstance(instance, Category):
        # First check if there's custom SEO data for this category
        try:
            if instance.seo and instance.seo.meta_title:
                return instance.seo.meta_title
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated title with optimization
        coupon_count = Coupon.objects.filter(category=instance, is_active=True).count()
        
        if coupon_count > 0:
            return f"{instance.name} Coupons: {coupon_count} Deals for {timezone.now().strftime('%B %Y')}"
        else:
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
        
        # Fall back to generated description with optimization
        truncated_desc = Truncator(strip_tags(instance.description)).words(25)
        expiry_date = instance.expiry_date.strftime('%b %d, %Y') if instance.expiry_date else 'No expiration'
        
        # Create a compelling description with call-to-action
        return f"Get {instance.discount_display} at {instance.store.name}. {truncated_desc} Valid until {expiry_date}. Click to save now!"
    
    elif isinstance(instance, Store):
        # First check if there's custom SEO data for this store
        try:
            if instance.seo and instance.seo.meta_description:
                return instance.seo.meta_description
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated description with optimization
        coupon_count = Coupon.objects.filter(store=instance, is_active=True).count()
        
        # Create a compelling description with social proof
        return f"Find {coupon_count} verified {instance.name} coupons, promo codes and deals for {timezone.now().strftime('%B %Y')}. Save money today with our exclusive discounts!"
    
    elif isinstance(instance, Category):
        # First check if there's custom SEO data for this category
        try:
            if instance.seo and instance.seo.meta_description:
                return instance.seo.meta_description
        except SEO.DoesNotExist:
            pass
            
        # Fall back to generated description with optimization
        coupon_count = Coupon.objects.filter(category=instance, is_active=True).count()
        
        # Create a compelling description with urgency
        return f"Browse {coupon_count} {instance.name} coupons and deals from top brands. Limited time offers - save money today!"
    
    # Return None instead of falling back to homepage
    return None

def get_meta_keywords(instance, request=None):
    """Get meta keywords for different models, using manual SEO data if available"""
    if isinstance(instance, Coupon):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        
        # Generate optimized keywords
        store_name = instance.store.name
        category_name = instance.category.name if instance.category else ""
        coupon_title = instance.title
        
        if category_name:
            return f"{store_name}, {category_name}, {coupon_title}, coupon, promo code, discount, deal, offer, save money, {timezone.now().strftime('%B %Y')}"
        else:
            return f"{store_name}, {coupon_title}, coupon, promo code, discount, deal, offer, save money, {timezone.now().strftime('%B %Y')}"
    
    elif isinstance(instance, Store):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        
        # Generate optimized keywords
        return f"{instance.name}, coupons, promo codes, deals, discounts, savings, offers, {timezone.now().strftime('%B %Y')}"
    
    elif isinstance(instance, Category):
        if hasattr(instance, 'seo') and instance.seo and instance.seo.meta_keywords:
            return instance.seo.meta_keywords
        
        # Generate optimized keywords
        return f"{instance.name}, coupons, deals, discounts, savings, promo codes, offers, {timezone.now().strftime('%B %Y')}"
    
    # Return None instead of falling back to homepage
    return None

def get_open_graph_data(instance, request):
    """Generate Open Graph data for social sharing, using manual SEO data if available"""
    # Get the site URL from the request if available, otherwise use settings
    if request:
        site_url = f"{request.scheme}://{request.get_host()}"
    else:
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://coupradise.com'
    
    # Get default image URL
    try:
        default_image = f"{site_url}{static('img/og-image.png')}"
    except:
        default_image = f"{site_url}/static/img/og-image.png"
    
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
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_og_image_url'):
                    if callable(instance.seo.get_og_image_url):
                        og_image = instance.seo.get_og_image_url()
                    else:
                        og_image = instance.seo.get_og_image_url
                elif hasattr(instance.seo, 'og_image'):
                    og_image = instance.seo.og_image
                
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_twitter_image_url'):
                    if callable(instance.seo.get_twitter_image_url):
                        twitter_image = instance.seo.get_twitter_image_url()
                    else:
                        twitter_image = instance.seo.get_twitter_image_url
                elif hasattr(instance.seo, 'twitter_image'):
                    twitter_image = instance.seo.twitter_image
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        if not og_title:
            og_title = f"Save {instance.discount_display} at {instance.store.name} - Limited Time Offer"
        
        if not og_description:
            og_description = f"Get {instance.discount_display} with this {instance.store.name} coupon. {Truncator(strip_tags(instance.description)).words(20)}"
            
        if not og_image:
            if instance.store.logo:
                # Ensure absolute URL for the logo
                if instance.store.logo.url.startswith(('http://', 'https://')):
                    og_image = instance.store.logo.url
                else:
                    og_image = f"{site_url}{instance.store.logo.url}"
            else:
                og_image = default_image
            
        if not twitter_title:
            twitter_title = og_title
            
        if not twitter_description:
            twitter_description = og_description
            
        if not twitter_image:
            twitter_image = og_image
        
        # Determine section based on coupon type
        section = 'coupons'  # Default section
        if instance.source == 'AMAZON':
            section = 'amazon'
        elif instance.is_special:
            section = 'special'
        elif instance.coupon_type == 'DEAL':
            section = 'deals'
        
        return {
            'og_title': og_title,
            'og_description': og_description,
            'og_url': f"{site_url}{reverse('deal_detail', kwargs={'section': section, 'slug': instance.slug})}",
            'og_image': og_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': twitter_title,
            'twitter_description': twitter_description,
            'twitter_image': twitter_image,
            'twitter_card': 'summary_large_image',
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
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_og_image_url'):
                    if callable(instance.seo.get_og_image_url):
                        og_image = instance.seo.get_og_image_url()
                    else:
                        og_image = instance.seo.get_og_image_url
                elif hasattr(instance.seo, 'og_image'):
                    og_image = instance.seo.og_image
                
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_twitter_image_url'):
                    if callable(instance.seo.get_twitter_image_url):
                        twitter_image = instance.seo.get_twitter_image_url()
                    else:
                        twitter_image = instance.seo.get_twitter_image_url
                elif hasattr(instance.seo, 'twitter_image'):
                    twitter_image = instance.seo.twitter_image
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        coupon_count = Coupon.objects.filter(store=instance, is_active=True).count()
        
        if not og_title:
            og_title = f"{instance.name} Coupons & Promo Codes - {coupon_count} Active Offers"
        
        if not og_description:
            og_description = f"Save money with {coupon_count} verified {instance.name} coupons and deals. Exclusive discounts for {timezone.now().strftime('%B %Y')}."
            
        if not og_image:
            if instance.logo:
                # Ensure absolute URL for the logo
                if instance.logo.url.startswith(('http://', 'https://')):
                    og_image = instance.logo.url
                else:
                    og_image = f"{site_url}{instance.logo.url}"
            else:
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
            'og_url': f"{site_url}{reverse('store_detail', kwargs={'store_slug': instance.slug})}",
            'og_image': og_image,
            'og_type': 'website',
            'og_site_name': 'CouPradise',
            'twitter_title': twitter_title,
            'twitter_description': twitter_description,
            'twitter_image': twitter_image,
            'twitter_card': 'summary_large_image',
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
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_og_image_url'):
                    if callable(instance.seo.get_og_image_url):
                        og_image = instance.seo.get_og_image_url()
                    else:
                        og_image = instance.seo.get_og_image_url
                elif hasattr(instance.seo, 'og_image'):
                    og_image = instance.seo.og_image
                
                twitter_title = instance.seo.twitter_title
                twitter_description = instance.seo.twitter_description
                
                # Handle both methods and fields for image URLs
                if hasattr(instance.seo, 'get_twitter_image_url'):
                    if callable(instance.seo.get_twitter_image_url):
                        twitter_image = instance.seo.get_twitter_image_url()
                    else:
                        twitter_image = instance.seo.get_twitter_image_url
                elif hasattr(instance.seo, 'twitter_image'):
                    twitter_image = instance.seo.twitter_image
        except SEO.DoesNotExist:
            pass
        
        # If no custom data, generate it
        coupon_count = Coupon.objects.filter(category=instance, is_active=True).count()
        
        if not og_title:
            og_title = f"{instance.name} Coupons & Deals - {coupon_count} Active Offers"
        
        if not og_description:
            og_description = f"Find the best {instance.name} coupons and deals. {coupon_count} verified discounts for {timezone.now().strftime('%B %Y')}."
            
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
            'twitter_card': 'summary_large_image',
        }
    
    # Return None instead of falling back to homepage
    return None

def get_breadcrumbs(instance):
    """Generate breadcrumb navigation for different models"""
    breadcrumbs = [{'name': 'Home', 'url': '/'}]
    
    if isinstance(instance, Coupon):
        breadcrumbs.append({'name': 'Stores', 'url': reverse('all_stores')})
        breadcrumbs.append({'name': instance.store.name, 'url': reverse('store_detail', kwargs={'store_slug': instance.store.slug})})
        if instance.category:
            breadcrumbs.insert(2, {'name': instance.category.name, 'url': reverse('category_detail', kwargs={'category_slug': instance.category.slug})})
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
        # Determine section based on coupon type
        section = 'coupons'  # Default section
        if instance.source == 'AMAZON':
            section = 'amazon'
        elif instance.is_special:
            section = 'special'
        elif instance.coupon_type == 'DEAL':
            section = 'deals'
            
        return {
            "@context": "https://schema.org/",
            "@type": "Offer",
            "name": instance.title,
            "description": strip_tags(instance.description),
            "url": f"{settings.SITE_URL}{reverse('deal_detail', kwargs={'section': section, 'slug': instance.slug})}",
            "availability": "https://schema.org/InStock" if instance.is_active and not instance.is_expired else "https://schema.org/OutOfStock",
            "validFrom": instance.start_date.isoformat(),
            "validThrough": instance.expiry_date.isoformat() if instance.expiry_date else None,
            "discount": instance.discount_display,
            "provider": {
                "@type": "Organization",
                "name": instance.store.name,
                "url": instance.store.website,
                "logo": instance.store.logo.url if instance.store.logo else None
            },
            "category": instance.category.name if instance.category else "",
            "priceCurrency": "USD",
            "itemOffered": {
                "@type": "Service",
                "name": f"{instance.store.name} Discount"
            }
        }
    elif isinstance(instance, Store):
        return {
            "@context": "https://schema.org/",
            "@type": "Store",
            "name": instance.name,
            "description": strip_tags(instance.description),
            "url": instance.website,
            "logo": instance.logo.url if instance.logo else None,
            "image": instance.logo.url if instance.logo else None,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "US"
            },
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "reviewCount": "100"
            },
            "priceRange": "$"
        }
    elif isinstance(instance, Category):
        return {
            "@context": "https://schema.org/",
            "@type": "Thing",
            "name": instance.name,
            "description": strip_tags(instance.description),
            "url": f"{settings.SITE_URL}{reverse('category_detail', kwargs={'category_slug': instance.slug})}"
        }
    return None

def get_canonical_url(instance, request):
    """Generate canonical URL for different models"""
    if request:
        site_url = f"{request.scheme}://{request.get_host()}"
    else:
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://coupradise.com'
    
    if isinstance(instance, Coupon):
        # Determine section based on coupon type
        section = 'coupons'  # Default section
        if instance.source == 'AMAZON':
            section = 'amazon'
        elif instance.is_special:
            section = 'special'
        elif instance.coupon_type == 'DEAL':
            section = 'deals'
            
        return f"{site_url}{reverse('deal_detail', kwargs={'section': section, 'slug': instance.slug})}"
    elif isinstance(instance, Store):
        return f"{site_url}{reverse('store_detail', kwargs={'store_slug': instance.slug})}"
    elif isinstance(instance, Category):
        return f"{site_url}{reverse('category_detail', kwargs={'category_slug': instance.slug})}"
    
    return site_url