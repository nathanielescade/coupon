from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import URLValidator
import uuid


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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
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
    provider = models.ForeignKey(CouponProvider, on_delete=models.CASCADE, related_name='coupons', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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