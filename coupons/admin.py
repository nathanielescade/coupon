from django.contrib import admin
from .models import Coupon, CouponProvider, Store, Category, UserCoupon, CouponUsage

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
    list_display = ('title', 'store', 'category', 'discount_type', 'discount_value', 'expiry_date', 'is_active', 'is_featured', 'is_verified', 'created_at')
    list_filter = ('store', 'category', 'discount_type', 'coupon_type', 'is_active', 'is_featured', 'is_verified', 'created_at')
    search_fields = ('title', 'description', 'code')
    readonly_fields = ('id', 'usage_count', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'saved_at', 'is_used')
    list_filter = ('is_used', 'saved_at')
    search_fields = ('user__username', 'coupon__title')
    readonly_fields = ('saved_at',)

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'used_at', 'ip_address')
    list_filter = ('used_at',)
    search_fields = ('coupon__title', 'user__username', 'ip_address')
    readonly_fields = ('used_at',)



from django.contrib import admin
from .models import NewsletterSubscriber




from django.contrib import admin
from .models import NewsletterSubscriber, Newsletter

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