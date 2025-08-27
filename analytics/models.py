from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import user_agents

class PageView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    path = models.CharField(max_length=255)
    full_path = models.TextField()
    referer = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Device and browser info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    is_mobile = models.BooleanField(default=False)
    is_tablet = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False)
    
    # Location info (optional, would require a geoip service)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['path']),
        ]
    
    def __str__(self):
        return f"{self.path} at {self.timestamp}"
    
    def parse_user_agent(self):
        if self.user_agent:
            ua_string = self.user_agent
            user_agent_obj = user_agents.parse(ua_string)
            
            self.browser = user_agent_obj.browser.family
            self.browser_version = user_agent_obj.browser.version_string
            self.operating_system = user_agent_obj.os.family
            self.device_type = user_agent_obj.device.family
            self.is_mobile = user_agent_obj.is_mobile
            self.is_tablet = user_agent_obj.is_tablet
            self.is_pc = user_agent_obj.is_pc
            
            self.save(update_fields=[
                'browser', 'browser_version', 'operating_system', 
                'device_type', 'is_mobile', 'is_tablet', 'is_pc'
            ])

class Event(models.Model):
    EVENT_TYPES = [
        ('click', 'Click'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('save_offer', 'Save Offer'),
        ('copy_code', 'Copy Code'),
        ('view_offer', 'View Offer'),
        ('use_offer', 'Use Offer'),
        ('scroll', 'Scroll'),
        ('page_view', 'Page View'),
        ('form_submit', 'Form Submit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    page = models.CharField(max_length=255, blank=True)
    element = models.CharField(max_length=255, blank=True)
    data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} on {self.page} at {self.timestamp}"

class Session(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    page_views = models.PositiveIntegerField(default=0)
    duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user']),
            models.Index(fields=['start_time']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id}"
    
    def update_duration(self):
        if self.last_activity and self.start_time:
            self.duration = self.last_activity - self.start_time
            self.save(update_fields=['duration'])

# Renamed from CouponAnalytics to OfferAnalytics to match imports in views
class OfferAnalytics(models.Model):
    offer = models.ForeignKey('coupons.Coupon', on_delete=models.CASCADE, related_name='analytics')
    views = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    code_copies = models.PositiveIntegerField(default=0)
    uses = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Offer Analytics"
    
    def __str__(self):
        return f"Analytics for {self.offer.title}"
    
    def increment_views(self):
        self.views += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['views', 'last_viewed'])
    
    def increment_saves(self):
        self.saves += 1
        self.save(update_fields=['saves'])
    
    def increment_code_copies(self):
        self.code_copies += 1
        self.save(update_fields=['code_copies'])
    
    def increment_uses(self):
        self.uses += 1
        self.save(update_fields=['uses'])

class StoreAnalytics(models.Model):
    store = models.ForeignKey('coupons.Store', on_delete=models.CASCADE, related_name='analytics')
    views = models.PositiveIntegerField(default=0)
    offer_clicks = models.PositiveIntegerField(default=0)  # Renamed from coupon_clicks
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Store Analytics"
    
    def __str__(self):
        return f"Analytics for {self.store.name}"
    
    def increment_views(self):
        self.views += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['views', 'last_viewed'])
    
    def increment_offer_clicks(self):  # Renamed from increment_coupon_clicks
        self.offer_clicks += 1
        self.save(update_fields=['offer_clicks'])

class CategoryAnalytics(models.Model):
    category = models.ForeignKey('coupons.Category', on_delete=models.CASCADE, related_name='analytics')
    views = models.PositiveIntegerField(default=0)
    offer_clicks = models.PositiveIntegerField(default=0)  # Renamed from coupon_clicks
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Category Analytics"
    
    def __str__(self):
        return f"Analytics for {self.category.name}"
    
    def increment_views(self):
        self.views += 1
        self.last_viewed = timezone.now()
        self.save(update_fields=['views', 'last_viewed'])
    
    def increment_offer_clicks(self):  # Renamed from increment_coupon_clicks
        self.offer_clicks += 1
        self.save(update_fields=['offer_clicks'])

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity')
    session_id = models.CharField(max_length=255, blank=True)
    activity_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"