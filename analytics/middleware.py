import uuid
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from .models import PageView, Session, UserActivity

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or get session ID
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        # Get or create session record
        session, created = Session.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user if request.user.is_authenticated else None,
                'start_time': timezone.now(),
                'last_activity': timezone.now(),
            }
        )
        
        if not created:
            session.last_activity = timezone.now()
            session.page_views += 1
            session.save(update_fields=['last_activity', 'page_views'])
        
        # Store session ID in request for later use
        request.analytics_session_id = session_id
        
        # Process request
        response = self.get_response(request)
        
        # Track page view (excluding static files and API calls)
        if not request.path.startswith('/static/') and not request.path.startswith('/api/'):
            # Get user agent info
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create page view record
            page_view = PageView(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                path=request.path,
                full_path=request.get_full_path(),
                referer=request.META.get('HTTP_REFERER', ''),
                ip_address=self.get_client_ip(request),
                user_agent=user_agent,
            )
            page_view.save()
            
            # Parse user agent info
            page_view.parse_user_agent()
            
            # Update or create analytics records for specific pages
            self.update_analytics_records(request, page_view)
            
            # Log user activity
            if request.user.is_authenticated:
                UserActivity.objects.create(
                    user=request.user,
                    session_id=session_id,
                    activity_type='page_view',
                    description=f"Viewed {request.path}",
                    data={'path': request.path, 'method': request.method}
                )
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # analytics/middleware.py
    def update_analytics_records(self, request, page_view):
        from coupons.models import Coupon, Store, Category
        from .models import CouponAnalytics, StoreAnalytics, CategoryAnalytics
        
        path = request.path
        
        # Track coupon views
        if path.startswith('/coupon/') and len(path.split('/')) >= 3:
            try:
                slug = path.split('/')[2]
                # Check if the ID is a valid UUID before querying
                try:
                    uuid.UUID(slug)
                    # If it's a valid UUID, try to get the coupon
                    coupon = Coupon.objects.get(slug=slug)
                    coupon_analytics, created = CouponAnalytics.objects.get_or_create(coupon=coupon)
                    coupon_analytics.increment_views()
                except ValueError:
                    # Not a valid UUID, skip analytics tracking
                    pass
            except (Coupon.DoesNotExist, ValueError):
                pass
        
        # Track store views
        if path.startswith('/store/') and len(path.split('/')) >= 3:
            try:
                store_slug = path.split('/')[2]
                store = Store.objects.get(slug=store_slug)
                store_analytics, created = StoreAnalytics.objects.get_or_create(store=store)
                store_analytics.increment_views()
            except (Store.DoesNotExist, ValueError):
                pass
        
        # Track category views
        if path.startswith('/category/') and len(path.split('/')) >= 3:
            try:
                category_slug = path.split('/')[2]
                category = Category.objects.get(slug=category_slug)
                category_analytics, created = CategoryAnalytics.objects.get_or_create(category=category)
                category_analytics.increment_views()
            except (Category.DoesNotExist, ValueError):
                pass