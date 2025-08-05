from django.core.management.base import BaseCommand
from django.utils import timezone
from coupons.models import CouponProvider, Coupon, Store, Category
from django.contrib.auth.models import User
import requests
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch coupons from providers'

    def handle(self, *args, **options):
        providers = CouponProvider.objects.filter(is_active=True)
        
        if not providers:
            self.stdout.write(self.style.WARNING('No active coupon providers found.'))
            return
        
        for provider in providers:
            self.stdout.write(f'Fetching coupons from {provider.name}...')
            
            try:
                headers = {}
                if provider.api_key:
                    headers['Authorization'] = f'Bearer {provider.api_key}'
                
                response = requests.get(provider.api_url, headers=headers)
                response.raise_for_status()
                
                coupons_data = response.json()
                created_count = 0
                updated_count = 0
                
                # Get or create a default user for system-created coupons
                system_user, _ = User.objects.get_or_create(
                    username='system',
                    defaults={
                        'email': 'system@couponapp.com',
                        'is_staff': True,
                        'is_superuser': True,
                    }
                )
                
                for coupon_data in coupons_data:
                    # Get or create store
                    store, store_created = Store.objects.get_or_create(
                        name=coupon_data.get('store_name', 'Unknown'),
                        defaults={
                            'website': coupon_data.get('store_website', ''),
                            'slug': coupon_data.get('store_slug', ''),
                        }
                    )
                    
                    # Get or create category
                    category, category_created = Category.objects.get_or_create(
                        name=coupon_data.get('category_name', 'General'),
                        defaults={
                            'slug': coupon_data.get('category_slug', ''),
                        }
                    )
                    
                    # Create or update coupon
                    coupon, created = Coupon.objects.update_or_create(
                        title=coupon_data.get('title', ''),
                        defaults={
                            'description': coupon_data.get('description', ''),
                            'code': coupon_data.get('code', ''),
                            'coupon_type': coupon_data.get('coupon_type', 'CODE'),
                            'discount_type': coupon_data.get('discount_type', 'PERCENTAGE'),
                            'discount_value': coupon_data.get('discount_value'),
                            'minimum_purchase': coupon_data.get('minimum_purchase'),
                            'start_date': coupon_data.get('start_date', timezone.now()),
                            'expiry_date': coupon_data.get('expiry_date'),
                            'affiliate_link': coupon_data.get('affiliate_link', ''),
                            'store': store,
                            'category': category,
                            'provider': provider,
                            'created_by': system_user,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully fetched {created_count} new and {updated_count} updated coupons from {provider.name}.'
                    )
                )
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to fetch coupons from {provider.name}: {str(e)}'
                    )
                )
                logger.error(f'Failed to fetch coupons from {provider.name}: {str(e)}')