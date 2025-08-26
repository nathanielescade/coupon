from django.core.management.base import BaseCommand
from django.utils import timezone
from coupons.models import CouponProvider, Coupon, Store, Category
from django.contrib.auth.models import User
import random
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create sample data for the coupon app'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create a system user if it doesn't exist
        system_user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@couponapp.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Create sample coupon providers
        providers_data = [
            {
                'name': 'CouponAPI',
                'api_url': 'https://api.couponapi.com/v1/coupons',
                'api_key': 'sample_key_123',
            },
            {
                'name': 'DealsSource',
                'api_url': 'https://api.dealssource.com/coupons',
                'api_key': 'sample_key_456',
            },
        ]
        
        for provider_data in providers_data:
            provider, created = CouponProvider.objects.get_or_create(
                name=provider_data['name'],
                defaults={
                    'api_url': provider_data['api_url'],
                    'api_key': provider_data['api_key'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created provider: {provider.name}'))
        
        # Create sample stores
        stores_data = [
            {
                'name': 'Amazon',
                'slug': 'amazon',
                'website': 'https://www.amazon.com',
                'description': 'Online shopping for electronics, apparel, computers, books, DVDs & more'
            },
            {
                'name': 'Walmart',
                'slug': 'walmart',
                'website': 'https://www.walmart.com',
                'description': 'Save money. Live better. Online shopping for the latest electronics, fashion, home essentials & more.'
            },
            {
                'name': 'Target',
                'slug': 'target',
                'website': 'https://www.target.com',
                'description': 'Expect More. Pay Less. Free shipping on orders of $35+ or free same-day store pick-up.'
            },
            {
                'name': 'Best Buy',
                'slug': 'best-buy',
                'website': 'https://www.bestbuy.com',
                'description': 'Shop Best Buy for electronics, computers, appliances, cell phones, video games & more new tech.'
            },
            {
                'name': 'eBay',
                'slug': 'ebay',
                'website': 'https://www.ebay.com',
                'description': 'Buy and sell electronics, cars, fashion apparel, collectibles, sporting goods, digital cameras, baby items, coupons, and everything else on eBay.'
            },
        ]
        
        for store_data in stores_data:
            store, created = Store.objects.get_or_create(
                slug=store_data['slug'],
                defaults={
                    'name': store_data['name'],
                    'website': store_data['website'],
                    'description': store_data['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created store: {store.name}'))
        
        # Create sample categories
        categories_data = [
            {
                'name': 'Electronics',
                'slug': 'electronics',
                'description': 'Coupons for electronics and gadgets'
            },
            {
                'name': 'Fashion',
                'slug': 'fashion',
                'description': 'Clothing, shoes, and accessories coupons'
            },
            {
                'name': 'Home & Garden',
                'slug': 'home-garden',
                'description': 'Furniture, decor, and garden supplies'
            },
            {
                'name': 'Food & Dining',
                'slug': 'food-dining',
                'description': 'Restaurants, groceries, and food delivery'
            },
            {
                'name': 'Travel',
                'slug': 'travel',
                'description': 'Hotels, flights, and vacation packages'
            },
            {
                'name': 'Health & Beauty',
                'slug': 'health-beauty',
                'description': 'Cosmetics, skincare, and health products'
            },
        ]
        
        for category_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=category_data['slug'],
                defaults={
                    'name': category_data['name'],
                    'description': category_data['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        
        # Create sample coupons
        stores = list(Store.objects.all())
        categories = list(Category.objects.all())
        providers = list(CouponProvider.objects.all())
        
        if not stores or not categories:
            self.stdout.write(self.style.ERROR('No stores or categories found. Cannot create coupons.'))
            return
        
        coupons_data = [
            {
                'title': '20% Off Electronics',
                'description': 'Save 20% on all electronics items. Limited time offer.',
                'code': 'ELEC20',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 20.00,
                'minimum_purchase': 50.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=30),
                'is_featured': True,
                'is_verified': True,
                'usage_limit': 100,
            },
            {
                'title': '$10 Off Your First Order',
                'description': 'Get $10 off your first order of $25 or more.',
                'code': 'FIRST10',
                'coupon_type': 'CODE',
                'discount_type': 'FIXED',
                'discount_value': 10.00,
                'minimum_purchase': 25.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=14),
                'is_featured': True,
                'is_verified': True,
                'usage_limit': 200,
            },
            {
                'title': 'Free Shipping on All Orders',
                'description': 'No minimum purchase required. Free shipping for a limited time.',
                'code': 'FREESHIP',
                'coupon_type': 'FREE_SHIPPING',
                'discount_type': 'FREE',
                'discount_value': 0,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=7),
                'is_featured': False,
                'is_verified': True,
                'usage_limit': 500,
            },
            {
                'title': 'Buy One Get One Free',
                'description': 'Buy one item and get another one of equal or lesser value free.',
                'code': 'BOGO',
                'coupon_type': 'BOGO',
                'discount_type': 'BOGO',
                'discount_value': 0,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=21),
                'is_featured': True,
                'is_verified': True,
                'usage_limit': 100,
            },
            {
                'title': '15% Off Fashion Items',
                'description': 'Save 15% on all fashion items including clothing, shoes, and accessories.',
                'code': 'FASHION15',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 15.00,
                'minimum_purchase': 30.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=45),
                'is_featured': False,
                'is_verified': True,
                'usage_limit': 150,
            },
            {
                'title': '$5 Off Home & Garden',
                'description': 'Save $5 on all home and garden items. Minimum purchase of $20 required.',
                'code': 'HOME5',
                'coupon_type': 'CODE',
                'discount_type': 'FIXED',
                'discount_value': 5.00,
                'minimum_purchase': 20.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=10),
                'is_featured': False,
                'is_verified': True,
                'usage_limit': 75,
            },
            {
                'title': '30% Off Health & Beauty',
                'description': 'Save 30% on all health and beauty products. Limited time offer.',
                'code': 'HEALTH30',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 30.00,
                'minimum_purchase': 25.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=5),
                'is_featured': True,
                'is_verified': True,
                'usage_limit': 50,
            },
            {
                'title': 'Free Item with Purchase',
                'description': 'Get a free gift with any purchase of $50 or more.',
                'code': 'FREEGIFT',
                'coupon_type': 'FREE',
                'discount_type': 'FREE',
                'discount_value': 0,
                'minimum_purchase': 50.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=60),
                'is_featured': False,
                'is_verified': True,
                'usage_limit': 200,
            },
        ]
        
        for coupon_data in coupons_data:
            # Get random store, category, and provider
            store = random.choice(stores)
            category = random.choice(categories)
            provider = random.choice(providers) if providers else None
            
            # Create or update coupon
            coupon, created = Coupon.objects.get_or_create(
                title=coupon_data['title'],
                defaults={
                    'description': coupon_data['description'],
                    'code': coupon_data['code'],
                    'coupon_type': coupon_data['coupon_type'],
                    'discount_type': coupon_data['discount_type'],
                    'discount_value': coupon_data['discount_value'],
                    'minimum_purchase': coupon_data['minimum_purchase'],
                    'expiry_date': coupon_data['expiry_date'],
                    'is_featured': coupon_data['is_featured'],
                    'is_verified': coupon_data['is_verified'],
                    'usage_limit': coupon_data['usage_limit'],
                    'terms_and_conditions': 'Terms and conditions apply. See website for details.',
                    'affiliate_link': f'https://{store.website}/?ref=couponapp',
                    'store': store,
                    'category': category,
                    'provider': provider,
                    'created_by': system_user,
                }
            )
            
            # Generate and save slug for the coupon
            if not coupon.slug:
                coupon.slug = coupon.generate_slug()
                coupon.save()
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created coupon: {coupon.title} with slug: {coupon.slug}'))
            else:
                self.stdout.write(self.style.WARNING(f'Coupon already exists: {coupon.title} with slug: {coupon.slug}'))
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))