from django.core.management.base import BaseCommand
from django.db import connection
from coupons.models import Coupon, Store, Category, SEO, HomePageSEO

class Command(BaseCommand):
    help = 'Verifies SEO data for all content types'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Verifying SEO data...'))
        
        # Check Homepage SEO
        try:
            homepage_seo = HomePageSEO.objects.get()
            self.stdout.write(self.style.SUCCESS(f'✓ Homepage SEO exists: {homepage_seo.meta_title}'))
        except HomePageSEO.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Homepage SEO does not exist'))
        
        # Check Store SEO
        stores = Store.objects.all()
        self.stdout.write(f'Checking {stores.count()} stores...')
        for store in stores:
            try:
                if store.seo:
                    self.stdout.write(self.style.SUCCESS(f'✓ Store "{store.name}" has SEO data'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Store "{store.name}" has no SEO data'))
            except SEO.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ Store "{store.name}" has no SEO data'))
        
        # Check Category SEO
        categories = Category.objects.all()
        self.stdout.write(f'Checking {categories.count()} categories...')
        for category in categories:
            try:
                if category.seo:
                    self.stdout.write(self.style.SUCCESS(f'✓ Category "{category.name}" has SEO data'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Category "{category.name}" has no SEO data'))
            except SEO.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ Category "{category.name}" has no SEO data'))
        
        # Check Coupon SEO
        coupons = Coupon.objects.all()
        self.stdout.write(f'Checking {coupons.count()} coupons...')
        for coupon in coupons:
            try:
                if coupon.seo:
                    self.stdout.write(self.style.SUCCESS(f'✓ Coupon "{coupon.title}" has SEO data'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Coupon "{coupon.title}" has no SEO data'))
            except SEO.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠ Coupon "{coupon.title}" has no SEO data'))
        
        self.stdout.write(self.style.SUCCESS('SEO verification complete!'))