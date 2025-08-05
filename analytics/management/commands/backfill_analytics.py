# analytics/management/commands/backfill_analytics.py
from django.core.management.base import BaseCommand
from analytics.models import CouponAnalytics, StoreAnalytics, CategoryAnalytics
from coupons.models import Coupon, Store, Category
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backfill analytics data for existing coupons, stores, and categories'
    
    def handle(self, *args, **options):
        # Backfill coupon analytics
        self.stdout.write('Backfilling coupon analytics...')
        coupons = Coupon.objects.all()
        for coupon in coupons:
            analytics, created = CouponAnalytics.objects.get_or_create(coupon=coupon)
            if created:
                self.stdout.write(f'Created analytics for coupon: {coupon.title}')
        
        # Backfill store analytics
        self.stdout.write('Backfilling store analytics...')
        stores = Store.objects.all()
        for store in stores:
            analytics, created = StoreAnalytics.objects.get_or_create(store=store)
            if created:
                self.stdout.write(f'Created analytics for store: {store.name}')
        
        # Backfill category analytics
        self.stdout.write('Backfilling category analytics...')
        categories = Category.objects.all()
        for category in categories:
            analytics, created = CategoryAnalytics.objects.get_or_create(category=category)
            if created:
                self.stdout.write(f'Created analytics for category: {category.name}')
        
        self.stdout.write(self.style.SUCCESS('Analytics backfill complete!'))