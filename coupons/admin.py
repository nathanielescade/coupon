from django.contrib import admin
from .models import (
    Coupon, CouponProvider, Store, Category, UserOffer, OfferUsage, 
    NewsletterSubscriber, Newsletter, SEO, HomePageSEO, Tag
)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CouponProvider)
class CouponProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'api_url')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'website', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'website')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('title', 'store', 'category', 'discount_type', 'discount_value', 
                   'expiry_date', 'is_active', 'is_featured', 'is_verified', 'source', 'created_at')
    list_filter = ('store', 'category', 'discount_type', 'coupon_type', 'source', 
                  'is_active', 'is_featured', 'is_verified', 'is_special', 'is_popular', 'created_at')
    search_fields = ('title', 'description', 'code', 'slug')
    readonly_fields = ('id', 'usage_count', 'created_at', 'updated_at', 'slug')
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'store', 'category', 'provider', 'tags')
        }),
        ('Coupon Details', {
            'fields': ('code', 'coupon_type', 'discount_type', 'discount_value', 'minimum_purchase')
        }),
        ('Dates', {
            'fields': ('start_date', 'expiry_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_verified', 'is_special', 'is_popular')
        }),
        ('Usage', {
            'fields': ('usage_limit', 'usage_count', 'terms_and_conditions')
        }),
        ('Affiliate', {
            'fields': ('source', 'affiliate_link',)
        }),
        ('SEO', {
            'fields': ('seo',)
        }),
    )

@admin.register(UserOffer)
class UserOfferAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'saved_at', 'is_used')
    list_filter = ('is_used', 'saved_at')
    search_fields = ('user__username', 'offer__title')
    readonly_fields = ('saved_at',)

@admin.register(OfferUsage)
class OfferUsageAdmin(admin.ModelAdmin):
    list_display = ('offer', 'user', 'used_at', 'ip_address')
    list_filter = ('used_at',)
    search_fields = ('offer__title', 'user__username', 'ip_address')
    readonly_fields = ('used_at',)

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscribers were successfully activated.')
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscribers were successfully deactivated.')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_at', 'sent_at', 'is_sent']
    list_filter = ['is_sent', 'created_at', 'sent_at']
    search_fields = ['subject', 'content']
    readonly_fields = ['created_at', 'sent_at', 'is_sent']
    
    actions = ['send_newsletter_action']
    
    def send_newsletter_action(self, request, queryset):
        for newsletter in queryset:
            if not newsletter.is_sent:
                success, message = newsletter.send_newsletter()
                if success:
                    self.message_user(request, f"Newsletter '{newsletter.subject}' sent successfully. {message}")
                else:
                    self.message_user(request, f"Failed to send newsletter '{newsletter.subject}': {message}", level='error')
            else:
                self.message_user(request, f"Newsletter '{newsletter.subject}' was already sent on {newsletter.sent_at}", level='warning')
    send_newsletter_action.short_description = "Send selected newsletters"

@admin.register(SEO)
class SEOAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'content_id', 'meta_title', 'created_at', 'updated_at')
    list_filter = ('content_type', 'created_at', 'no_index', 'no_follow')
    search_fields = ('meta_title', 'meta_description', 'meta_keywords', 'content_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('content_type', 'content_id')
        }),
        ('Basic SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image', 'og_image_upload')
        }),
        ('Twitter Card', {
            'fields': ('twitter_title', 'twitter_description', 'twitter_image', 'twitter_image_upload')
        }),
        ('Advanced', {
            'fields': ('canonical_url', 'no_index', 'no_follow')
        }),
    )

@admin.register(HomePageSEO)
class HomePageSEOAdmin(admin.ModelAdmin):
    list_display = ('meta_title', 'hero_title', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    # Prevent creation of multiple instances
    def has_add_permission(self, request):
        # Check if there's already an instance
        if HomePageSEO.objects.exists():
            return False
        return super().has_add_permission(request)
    
    fieldsets = (
        ('Basic SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Open Graph', {
            'fields': ('og_title', 'og_description', 'og_image', 'og_image_upload')
        }),
        ('Twitter Card', {
            'fields': ('twitter_title', 'twitter_description', 'twitter_image', 'twitter_image_upload')
        }),
        ('Advanced', {
            'fields': ('canonical_url', 'no_index', 'no_follow')
        }),
        ('Homepage Content', {
            'fields': ('hero_title', 'hero_description')
        }),
    )