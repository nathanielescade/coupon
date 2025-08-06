from django.apps import AppConfig

class CouponsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coupons'
    
    def ready(self):
        # Import and connect signals
        import coupons.signals
        # Explicitly reference the signals to avoid "unused import" warnings
        coupons.signals.invalidate_coupon_cache
        coupons.signals.invalidate_store_cache
        coupons.signals.invalidate_category_cache