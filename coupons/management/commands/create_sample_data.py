from django.core.management.base import BaseCommand
from django.utils import timezone
from coupons.models import CouponProvider, Coupon, Store, Category, Tag, DealSection, DealHighlight
from django.contrib.auth.models import User
from django.utils.text import slugify
import random
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create sample data for the deals-focused coupon app'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create a system user if it doesn't exist
        system_user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@coupradise.com',
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
            {
                'name': 'Nike',
                'slug': 'nike',
                'website': 'https://www.nike.com',
                'description': 'Nike delivers innovative products, experiences and services to inspire athletes.'
            },
            {
                'name': 'Adidas',
                'slug': 'adidas',
                'website': 'https://www.adidas.com',
                'description': 'Adidas offers a range of sports clothing, shoes, and accessories for men, women, and children.'
            },
            {
                'name': 'Sephora',
                'slug': 'sephora',
                'website': 'https://www.sephora.com',
                'description': 'Sephora offers beauty products including makeup, skincare, fragrance, and haircare.'
            },
            {
                'name': 'Home Depot',
                'slug': 'home-depot',
                'website': 'https://www.homedepot.com',
                'description': 'Shop online for all your home improvement needs: appliances, bathroom decorating ideas, kitchen remodeling, patio furniture, power tools, bbq grills, carpeting, lumber, concrete, lighting, ceiling fans and more at The Home Depot.'
            },
            {
                'name': 'Expedia',
                'slug': 'expedia',
                'website': 'https://www.expedia.com',
                'description': 'Expedia makes finding cheap flights easy. Select from thousands of flights, airline tickets, and airfare deals worldwide.'
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
                'description': 'Deals for electronics and gadgets'
            },
            {
                'name': 'Fashion',
                'slug': 'fashion',
                'description': 'Clothing, shoes, and accessories deals'
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
            {
                'name': 'Sports & Outdoors',
                'slug': 'sports-outdoors',
                'description': 'Sporting goods and outdoor equipment'
            },
            {
                'name': 'Toys & Games',
                'slug': 'toys-games',
                'description': 'Toys, games, and hobbies'
            },
            {
                'name': 'Automotive',
                'slug': 'automotive',
                'description': 'Car parts, accessories, and services'
            },
            {
                'name': 'Books & Media',
                'slug': 'books-media',
                'description': 'Books, movies, music, and games'
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
        
        # Create sample tags
        tags_data = [
            {'name': 'Summer Sale'},
            {'name': 'Black Friday'},
            {'name': 'Cyber Monday'},
            {'name': 'Clearance'},
            {'name': 'New Customer'},
            {'name': 'Limited Time'},
            {'name': 'Free Shipping'},
            {'name': 'Best Seller'},
            {'name': 'Trending'},
            {'name': 'Exclusive'},
        ]
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'slug': slugify(tag_data['name']),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created tag: {tag.name}'))
        
        # Create deal sections
        deal_sections_data = [
            {
                'name': 'Special Offers',
                'slug': 'special-offers',
                'description': 'Exclusive special offers and limited-time deals'
            },
            {
                'name': 'Amazon Deals',
                'slug': 'amazon-deals',
                'description': 'Best deals from Amazon'
            },
            {
                'name': 'Hot Deals',
                'slug': 'hot-deals',
                'description': 'Trending deals and popular offers'
            },
            {
                'name': 'Coupon Codes',
                'slug': 'coupon-codes',
                'description': 'Discount codes and promo codes'
            },
            {
                'name': 'Seasonal Sales',
                'slug': 'seasonal-sales',
                'description': 'Seasonal promotions and holiday sales'
            },
        ]
        
        for section_data in deal_sections_data:
            section, created = DealSection.objects.get_or_create(
                slug=section_data['slug'],
                defaults={
                    'name': section_data['name'],
                    'description': section_data['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created deal section: {section.name}'))
        
        # Get all stores, categories, providers, and tags for creating coupons
        stores = list(Store.objects.all())
        categories = list(Category.objects.all())
        providers = list(CouponProvider.objects.all())
        tags = list(Tag.objects.all())
        deal_sections = list(DealSection.objects.all())
        
        if not stores or not categories:
            self.stdout.write(self.style.ERROR('No stores or categories found. Cannot create coupons.'))
            return
        
        # Create sample coupons with different types and sources
        coupons_data = [
            # Special Offers
            {
                'title': '50% Off Summer Fashion Collection',
                'description': 'Get 50% off on our entire summer fashion collection. Limited time offer.',
                'code': 'SUMMER50',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 50.00,
                'minimum_purchase': 50.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=30),
                'is_featured': True,
                'is_verified': True,
                'is_special': True,
                'is_popular': True,
                'usage_limit': 500,
                'source': 'DIRECT',
                'preferred_stores': ['nike', 'adidas'],
                'preferred_category': 'fashion',
                'preferred_tags': ['Summer Sale', 'Limited Time'],
            },
            {
                'title': 'Flash Sale: Electronics Up to 70% Off',
                'description': 'Flash sale on electronics with discounts up to 70%. Don\'t miss out!',
                'code': None,
                'coupon_type': 'DEAL',
                'discount_type': 'PERCENTAGE',
                'discount_value': 70.00,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=2),
                'is_featured': True,
                'is_verified': True,
                'is_special': True,
                'is_popular': True,
                'usage_limit': None,
                'source': 'DIRECT',
                'preferred_stores': ['best-buy', 'amazon'],
                'preferred_category': 'electronics',
                'preferred_tags': ['Limited Time', 'Trending'],
            },
            
            # Amazon Deals
            {
                'title': 'Amazon Prime Day: Exclusive Deals',
                'description': 'Exclusive Prime Day deals on Amazon for Prime members only.',
                'code': 'PRIME23',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 30.00,
                'minimum_purchase': 25.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=7),
                'is_featured': True,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': 1000,
                'source': 'AMAZON',
                'preferred_stores': ['amazon'],
                'preferred_tags': ['Exclusive', 'Limited Time'],
            },
            {
                'title': 'Amazon: Buy 2 Get 1 Free on Books',
                'description': 'Buy any two books and get one free on Amazon. Wide selection available.',
                'code': None,
                'coupon_type': 'DEAL',
                'discount_type': 'BOGO',
                'discount_value': 0,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=14),
                'is_featured': False,
                'is_verified': True,
                'is_special': False,
                'is_popular': False,
                'usage_limit': None,
                'source': 'AMAZON',
                'preferred_stores': ['amazon'],
                'preferred_category': 'books-media',
                'preferred_tags': ['Best Seller'],
            },
            
            # Hot Deals
            {
                'title': 'Weekend Special: $20 Off $100',
                'description': 'Get $20 off on purchases of $100 or more this weekend only.',
                'code': 'WEEKEND20',
                'coupon_type': 'CODE',
                'discount_type': 'FIXED',
                'discount_value': 20.00,
                'minimum_purchase': 100.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=3),
                'is_featured': True,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': 300,
                'source': 'DIRECT',
                'preferred_stores': ['walmart', 'target'],
                'preferred_tags': ['Limited Time', 'Trending'],
            },
            {
                'title': 'Home Appliances Sale: Up to 40% Off',
                'description': 'Save up to 40% on selected home appliances. Limited stock available.',
                'code': None,
                'coupon_type': 'DEAL',
                'discount_type': 'PERCENTAGE',
                'discount_value': 40.00,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=10),
                'is_featured': True,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': None,
                'source': 'DIRECT',
                'preferred_stores': ['home-depot'],
                'preferred_category': 'home-garden',
                'preferred_tags': ['Clearance', 'Trending'],
            },
            
            # Coupon Codes
            {
                'title': '15% Off Your First Order',
                'description': 'New customers get 15% off their first order. Sign up now!',
                'code': 'WELCOME15',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 15.00,
                'minimum_purchase': 25.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=30),
                'is_featured': False,
                'is_verified': True,
                'is_special': False,
                'is_popular': False,
                'usage_limit': 1000,
                'source': 'DIRECT',
                'preferred_tags': ['New Customer'],
            },
            {
                'title': 'Free Shipping on All Orders',
                'description': 'Get free shipping on all orders, no minimum purchase required.',
                'code': 'FREESHIP',
                'coupon_type': 'FREE_SHIPPING',
                'discount_type': 'FREE',
                'discount_value': 0,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=7),
                'is_featured': True,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': 2000,
                'source': 'DIRECT',
                'preferred_tags': ['Free Shipping'],
            },
            
            # More diverse offers
            {
                'title': 'Student Discount: 10% Off',
                'description': 'Students get 10% off on all orders. Valid student ID required.',
                'code': 'STUDENT10',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 10.00,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=90),
                'is_featured': False,
                'is_verified': True,
                'is_special': False,
                'is_popular': False,
                'usage_limit': 500,
                'source': 'DIRECT',
                'preferred_tags': ['Exclusive'],
            },
            {
                'title': 'Holiday Special: $25 Off $75',
                'description': 'Holiday special: Get $25 off on purchases of $75 or more.',
                'code': 'HOLIDAY25',
                'coupon_type': 'CODE',
                'discount_type': 'FIXED',
                'discount_value': 25.00,
                'minimum_purchase': 75.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=14),
                'is_featured': True,
                'is_verified': True,
                'is_special': True,
                'is_popular': True,
                'usage_limit': 750,
                'source': 'DIRECT',
                'preferred_tags': ['Seasonal Sales', 'Limited Time'],
            },
            {
                'title': 'Beauty Products: Buy 2 Get 1 Free',
                'description': 'Buy any two beauty products and get one free. Limited time offer.',
                'code': 'BEAUTYBOGO',
                'coupon_type': 'BOGO',
                'discount_type': 'BOGO',
                'discount_value': 0,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=21),
                'is_featured': False,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': 300,
                'source': 'DIRECT',
                'preferred_stores': ['sephora'],
                'preferred_category': 'health-beauty',
                'preferred_tags': ['Trending'],
            },
            {
                'title': 'Travel Deals: Up to 30% Off Hotels',
                'description': 'Save up to 30% on hotel bookings worldwide. Book now!',
                'code': None,
                'coupon_type': 'DEAL',
                'discount_type': 'PERCENTAGE',
                'discount_value': 30.00,
                'minimum_purchase': None,
                'expiry_date': timezone.now() + timezone.timedelta(days=5),
                'is_featured': True,
                'is_verified': True,
                'is_special': False,
                'is_popular': True,
                'usage_limit': None,
                'source': 'DIRECT',
                'preferred_stores': ['expedia'],
                'preferred_category': 'travel',
                'preferred_tags': ['Limited Time'],
            },
            {
                'title': 'Black Friday Preview: Early Access',
                'description': 'Get early access to our Black Friday deals. Exclusive for subscribers.',
                'code': 'BFWEEK',
                'coupon_type': 'CODE',
                'discount_type': 'PERCENTAGE',
                'discount_value': 25.00,
                'minimum_purchase': 50.00,
                'expiry_date': timezone.now() + timezone.timedelta(days=45),
                'is_featured': True,
                'is_verified': True,
                'is_special': True,
                'is_popular': True,
                'usage_limit': 1000,
                'source': 'DIRECT',
                'preferred_tags': ['Black Friday', 'Exclusive'],
            },
        ]
        
        created_coupons = []
        for coupon_data in coupons_data:
            # Get preferred store or random one
            if 'preferred_stores' in coupon_data:
                store_slugs = coupon_data['preferred_stores']
                preferred_stores = [s for s in stores if s.slug in store_slugs]
                store = random.choice(preferred_stores) if preferred_stores else random.choice(stores)
            else:
                store = random.choice(stores)
            
            # Get preferred category or random one
            if 'preferred_category' in coupon_data:
                category_slug = coupon_data['preferred_category']
                preferred_category = [c for c in categories if c.slug == category_slug]
                category = preferred_category[0] if preferred_category else random.choice(categories)
            else:
                category = random.choice(categories)
            
            # Get random provider
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
                    'is_active': True,
                    'is_featured': coupon_data['is_featured'],
                    'is_verified': coupon_data['is_verified'],
                    'is_special': coupon_data['is_special'],
                    'is_popular': coupon_data['is_popular'],
                    'usage_limit': coupon_data['usage_limit'],
                    'terms_and_conditions': 'Terms and conditions apply. See website for details.',
                    'affiliate_link': f'https://{store.website}/?ref=coupradise',
                    'source': coupon_data['source'],
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
            
            # Add tags if specified
            if 'preferred_tags' in coupon_data and tags:
                tag_names = coupon_data['preferred_tags']
                coupon_tags = [t for t in tags if t.name in tag_names]
                if coupon_tags:
                    coupon.tags.set(coupon_tags)
            
            if created:
                created_coupons.append(coupon)
                self.stdout.write(self.style.SUCCESS(f'Created coupon: {coupon.title} with slug: {coupon.slug}'))
            else:
                self.stdout.write(self.style.WARNING(f'Coupon already exists: {coupon.title} with slug: {coupon.slug}'))
        
        # Create deal highlights
        if created_coupons and deal_sections:
            # Get special offers section
            special_section = next((s for s in deal_sections if s.slug == 'special-offers'), None)
            amazon_section = next((s for s in deal_sections if s.slug == 'amazon-deals'), None)
            hot_deals_section = next((s for s in deal_sections if s.slug == 'hot-deals'), None)
            
            # Create highlights for special offers
            if special_section:
                special_coupons = [c for c in created_coupons if c.is_special][:3]
                for i, coupon in enumerate(special_coupons):
                    DealHighlight.objects.get_or_create(
                        deal=coupon,
                        section=special_section,
                        defaults={
                            'display_order': i,
                            'is_active': True,
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created highlight for special offer: {coupon.title}'))
            
            # Create highlights for Amazon deals
            if amazon_section:
                amazon_coupons = [c for c in created_coupons if c.source == 'AMAZON'][:3]
                for i, coupon in enumerate(amazon_coupons):
                    DealHighlight.objects.get_or_create(
                        deal=coupon,
                        section=amazon_section,
                        defaults={
                            'display_order': i,
                            'is_active': True,
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created highlight for Amazon deal: {coupon.title}'))
            
            # Create highlights for hot deals
            if hot_deals_section:
                hot_coupons = [c for c in created_coupons if c.is_popular and not c.is_special][:3]
                for i, coupon in enumerate(hot_coupons):
                    DealHighlight.objects.get_or_create(
                        deal=coupon,
                        section=hot_deals_section,
                        defaults={
                            'display_order': i,
                            'is_active': True,
                        }
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created highlight for hot deal: {coupon.title}'))
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))