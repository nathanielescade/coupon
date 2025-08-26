from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import URLValidator
from django.utils.text import slugify
import uuid
from django.db import IntegrityError

class SEO(models.Model):
    """Model for storing SEO metadata for different content types"""
    CONTENT_TYPES = [
        ('home', 'Homepage'),
        ('coupon', 'Coupon'),
        ('store', 'Store'),
        ('category', 'Category'),
        ('page', 'Static Page'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Basic SEO fields
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Open Graph fields
    og_title = models.CharField(max_length=255, blank=True)
    og_description = models.TextField(blank=True)
    og_image = models.URLField(blank=True)
    og_image_upload = models.ImageField(upload_to='seo/og_images/', blank=True, null=True)
    
    # Twitter Card fields
    twitter_title = models.CharField(max_length=255, blank=True)
    twitter_description = models.TextField(blank=True)
    twitter_image = models.URLField(blank=True)
    twitter_image_upload = models.ImageField(upload_to='seo/twitter_images/', blank=True, null=True)
    
    # Additional SEO options
    canonical_url = models.URLField(blank=True)
    no_index = models.BooleanField(default=False)
    no_follow = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('content_type', 'content_id')
        verbose_name = "SEO Metadata"
        verbose_name_plural = "SEO Metadata"
    
    def __str__(self):
        return f"SEO for {self.get_content_type_display()}: {self.content_id or 'Homepage'}"
    
    @property
    def get_og_image_url(self):
        """Return the OG image URL, prioritizing uploaded image over URL"""
        if self.og_image_upload:
            return self.og_image_upload.url
        return self.og_image
    
    @property
    def get_twitter_image_url(self):
        """Return the Twitter image URL, prioritizing uploaded image over URL"""
        if self.twitter_image_upload:
            return self.twitter_image_upload.url
        return self.twitter_image


class HomePageSEO(models.Model):
    """Model for homepage-specific SEO settings"""
    meta_title = models.CharField(max_length=255, default="CouPradise - Save Money with Exclusive Coupons")
    meta_description = models.TextField(default="Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.")
    meta_keywords = models.CharField(max_length=255, default="coupons, promo codes, deals, discounts, savings, coupon codes")
    
    # Open Graph fields
    og_title = models.CharField(max_length=255, default="CouPradise - Save Money with Exclusive Coupons")
    og_description = models.TextField(default="Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.")
    og_image = models.URLField(blank=True)
    og_image_upload = models.ImageField(upload_to='seo/og_images/', blank=True, null=True)
    
    # Twitter Card fields
    twitter_title = models.CharField(max_length=255, default="CouPradise - Save Money with Exclusive Coupons")
    twitter_description = models.TextField(default="Discover the best coupons, promo codes and deals from your favorite stores. Save money on your online shopping with CouPradise.")
    twitter_image = models.URLField(blank=True)
    twitter_image_upload = models.ImageField(upload_to='seo/twitter_images/', blank=True, null=True)
    
    # Additional SEO options
    canonical_url = models.URLField(blank=True)
    no_index = models.BooleanField(default=False)
    no_follow = models.BooleanField(default=False)
    
    # Homepage-specific content
    hero_title = models.CharField(max_length=255, default="Save Money with Exclusive Coupons")
    hero_description = models.TextField(default="Discover the best deals and discounts from your favorite stores.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Homepage SEO"
        verbose_name_plural = "Homepage SEO"
    
    def __str__(self):
        return "Homepage SEO Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and HomePageSEO.objects.exists():
            raise ValueError("Only one HomePageSEO instance can exist")
        return super().save(*args, **kwargs)
    
    @property
    def get_og_image_url(self):
        """Return the OG image URL, prioritizing uploaded image over URL"""
        if self.og_image_upload:
            return self.og_image_upload.url
        return self.og_image
    
    @property
    def get_twitter_image_url(self):
        """Return the Twitter image URL, prioritizing uploaded image over URL"""
        if self.twitter_image_upload:
            return self.twitter_image_upload.url
        return self.twitter_image


class CouponProvider(models.Model):
    name = models.CharField(max_length=100)
    api_url = models.URLField(validators=[URLValidator()])
    api_key = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Store(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    website = models.URLField(validators=[URLValidator()])
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    seo = models.OneToOneField(SEO, on_delete=models.SET_NULL, null=True, blank=True, related_name='store')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    seo = models.OneToOneField(SEO, on_delete=models.SET_NULL, null=True, blank=True, related_name='category')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name




class Coupon(models.Model):
    COUPON_TYPE_CHOICES = [
        ('CODE', 'Discount Code'),
        ('DEAL', 'Deal'),
        ('PRINTABLE', 'Printable Coupon'),
        ('FREE_SHIPPING', 'Free Shipping'),
    ]
    
    DISCOUNT_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('BOGO', 'Buy One Get One'),
        ('FREE', 'Free Item'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    code = models.CharField(max_length=100, blank=True, null=True)
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE_CHOICES, default='CODE')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='PERCENTAGE')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    terms_and_conditions = models.TextField(blank=True)
    affiliate_link = models.URLField(blank=True, null=True, validators=[URLValidator()])
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='coupons')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='coupons')
    seo = models.OneToOneField(SEO, on_delete=models.SET_NULL, null=True, blank=True, related_name='coupon')
    provider = models.ForeignKey(CouponProvider, on_delete=models.CASCADE, related_name='coupons', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Updated slug field with db_index for faster lookups
    # slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    @property
    def discount_display(self):
        if self.discount_type == 'PERCENTAGE':
            return f"{self.discount_value}% OFF"
        elif self.discount_type == 'FIXED':
            return f"${self.discount_value} OFF"
        elif self.discount_type == 'BOGO':
            return "Buy One Get One Free"
        elif self.discount_type == 'FREE':
            return "Free Item"
        return ""
    
    def generate_slug(self):
        """Generate a hybrid slug from title and UUID with improved formatting"""
        # Create a URL-friendly version of the title, limited to 200 chars
        title_slug = slugify(self.title)[:200]
        
        # Get the first 12 characters of the UUID using .hex for cleaner output
        uuid_str = self.id.hex[:12]  # Increased to 12 chars for better uniqueness
        
        # Combine them with a hyphen
        slug = f"{title_slug}-{uuid_str}"
        
        # Ensure uniqueness
        original_slug = slug
        counter = 1
        while Coupon.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
            
        return slug
    
    def save(self, *args, **kwargs):
        """Override save to generate slug if it doesn't exist, with retry mechanism"""
        if not self.slug:
            self.slug = self.generate_slug()
            
        # Try saving, and if we get a unique constraint error on slug, try again with a new slug
        max_retries = 5
        for attempt in range(max_retries):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError as e:
                if 'slug' in str(e) and 'UNIQUE constraint failed' in str(e) and attempt < max_retries - 1:
                    # Generate a new slug by appending a counter
                    base_slug = self.slug.rsplit('-', 1)[0]  # Remove the last part (UUID or counter)
                    self.slug = f"{base_slug}-{attempt + 1}"
                else:
                    raise e
                


class UserCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'coupon')
    
    def __str__(self):
        return f"{self.user.username} - {self.coupon.title}"


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    used_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    def __str__(self):
        return f"{self.coupon.title} used by {self.user.username}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email


class Newsletter(models.Model):
    subject = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.subject
    
    def send_newsletter(self):
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        from coupons.models import Coupon
        import datetime
        
        # Get latest coupons for the newsletter
        days_ago = 7
        start_date = timezone.now() - datetime.timedelta(days=days_ago)
        coupons = Coupon.objects.filter(
            is_active=True,
            created_at__gte=start_date
        ).order_by('-created_at')[:10]
        
        # Get subscribers
        subscribers = NewsletterSubscriber.objects.filter(is_active=True)
        
        if not subscribers.exists():
            return False, "No active subscribers found"
        
        # Send emails
        from_email = settings.DEFAULT_FROM_EMAIL
        success_count = 0
        error_count = 0
        
        for subscriber in subscribers:
            try:
                # Render HTML email
                html_content = render_to_string('custom_newsletter_email.html', {
                    'subject': self.subject,
                    'content': self.content,
                    'coupons': coupons,
                    'email': subscriber.email
                })
                
                # Create email message
                email = EmailMultiAlternatives(
                    self.subject,
                    f"{self.content}\n\nCheck out the latest deals and coupons on CouPradise!",
                    from_email,
                    [subscriber.email]
                )
                
                # Attach HTML version
                email.attach_alternative(html_content, "text/html")
                
                # Send email
                email.send()
                success_count += 1
                
            except Exception as e:
                error_count += 1
        
        # Update newsletter status
        self.sent_at = timezone.now()
        self.is_sent = True
        self.save()
        
        return True, f"Successfully sent to {success_count} subscribers, {error_count} failed"