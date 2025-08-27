from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncHour, TruncWeek, TruncMonth
from .models import PageView, Event, Session, OfferAnalytics, StoreAnalytics, CategoryAnalytics, UserActivity
from coupons.models import Coupon, Store, Category
import json
from django.http import JsonResponse

def is_admin_user(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin_user)
def analytics_dashboard(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Basic metrics
    total_page_views = PageView.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date).count()
    unique_visitors = PageView.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date).values('session_id').distinct().count()
    unique_users = PageView.objects.filter(timestamp__gte=start_date, timestamp__lte=end_date).exclude(user__isnull=True).values('user').distinct().count()
    
    # Page views by day
    page_views_by_day = PageView.objects.filter(
        timestamp__gte=start_date, 
        timestamp__lte=end_date
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Top pages
    top_pages = PageView.objects.filter(
        timestamp__gte=start_date, 
        timestamp__lte=end_date
    ).values('path').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Device types
    device_stats = {
        'mobile': PageView.objects.filter(
            timestamp__gte=start_date, 
            timestamp__lte=end_date,
            is_mobile=True
        ).count(),
        'tablet': PageView.objects.filter(
            timestamp__gte=start_date, 
            timestamp__lte=end_date,
            is_tablet=True
        ).count(),
        'desktop': PageView.objects.filter(
            timestamp__gte=start_date, 
            timestamp__lte=end_date,
            is_pc=True
        ).count(),
    }
    
    # Browser stats
    browser_stats = PageView.objects.filter(
        timestamp__gte=start_date, 
        timestamp__lte=end_date
    ).exclude(browser__isnull=True).exclude(browser='').values('browser').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Event stats
    event_stats = Event.objects.filter(
        timestamp__gte=start_date, 
        timestamp__lte=end_date
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top offers (renamed from coupons)
    top_offers = OfferAnalytics.objects.annotate(
        offer_title=F('offer__title')
    ).order_by('-views')[:10]
    
    # Top stores
    top_stores = StoreAnalytics.objects.annotate(
        store_name=F('store__name')
    ).order_by('-views')[:10]
    
    # Top categories
    top_categories = CategoryAnalytics.objects.annotate(
        category_name=F('category__name')
    ).order_by('-views')[:10]
    
    # User activity
    active_users = UserActivity.objects.filter(
        timestamp__gte=start_date, 
        timestamp__lte=end_date
    ).values('user__username').annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')[:10]
    
    # Session stats
    avg_session_duration = Session.objects.filter(
        start_time__gte=start_date,
        duration__isnull=False
    ).aggregate(
        avg_duration=Avg(ExpressionWrapper(F('duration'), output_field=DurationField()))
    )['avg_duration']
    
    # Prepare data for charts
    page_views_by_day_data = {
        'labels': [item['date'].strftime('%Y-%m-%d') for item in page_views_by_day],
        'data': [item['count'] for item in page_views_by_day]
    }
    
    device_stats_data = {
        'labels': list(device_stats.keys()),
        'data': list(device_stats.values())
    }
    
    browser_stats_data = {
        'labels': [item['browser'] for item in browser_stats],
        'data': [item['count'] for item in browser_stats]
    }
    
    event_stats_data = {
        'labels': [item['event_type'] for item in event_stats],
        'data': [item['count'] for item in event_stats]
    }
    
    context = {
        'days': days,
        'total_page_views': total_page_views,
        'unique_visitors': unique_visitors,
        'unique_users': unique_users,
        'page_views_by_day_json': json.dumps(page_views_by_day_data),
        'top_pages': top_pages,
        'device_stats_json': json.dumps(device_stats_data),
        'browser_stats_json': json.dumps(browser_stats_data),
        'event_stats_json': json.dumps(event_stats_data),
        'top_offers': top_offers,  # Renamed from top_coupons
        'top_stores': top_stores,
        'top_categories': top_categories,
        'active_users': active_users,
        'avg_session_duration': avg_session_duration,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def offer_analytics(request):  # Renamed from coupon_analytics
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all offers with their analytics
    offer_stats = []
    offers = Coupon.objects.all()  # Still using Coupon model
    
    for offer in offers:
        try:
            analytics = OfferAnalytics.objects.get(offer=offer)  # Changed from coupon to offer
            stats = {
                'id': offer.slug,
                'title': offer.title,
                'store': offer.store.name,
                'views': analytics.views,
                'saves': analytics.saves,
                'code_copies': analytics.code_copies,
                'uses': analytics.uses,
                'conversion_rate': 0,
            }
            
            # Calculate conversion rate (saves / views)
            if stats['views'] > 0:
                stats['conversion_rate'] = round((stats['saves'] / stats['views']) * 100, 2)
            
            offer_stats.append(stats)
        except OfferAnalytics.DoesNotExist:  # Changed from CouponAnalytics
            # If no analytics record exists, create one with default values
            analytics = OfferAnalytics.objects.create(offer=offer)  # Changed from coupon to offer
            stats = {
                'id': offer.slug,
                'title': offer.title,
                'store': offer.store.name,
                'views': 0,
                'saves': 0,
                'code_copies': 0,
                'uses': 0,
                'conversion_rate': 0,
            }
            offer_stats.append(stats)
    
    # Sort by views
    offer_stats.sort(key=lambda x: x['views'], reverse=True)
    
    context = {
        'days': days,
        'offer_stats': offer_stats,  # Renamed from coupon_stats
    }
    
    return render(request, 'analytics/offer_analytics.html', context)  # Updated template name

@login_required
@user_passes_test(is_admin_user)
def store_analytics(request):
    stores = Store.objects.all()
    
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    store_stats = []
    for store in stores:
        try:
            analytics = StoreAnalytics.objects.get(store=store)
            stats = {
                'id': store.id,
                'name': store.name,
                'views': analytics.views,
                'offer_clicks': analytics.offer_clicks,  # Changed from coupon_clicks
                'offer_count': store.coupons.count(),  # Renamed from coupon_count
            }
            
            # Calculate click-through rate
            if stats['views'] > 0:
                stats['ctr'] = round((stats['offer_clicks'] / stats['views']) * 100, 2)  # Changed from coupon_clicks
            else:
                stats['ctr'] = 0
            
            store_stats.append(stats)
        except StoreAnalytics.DoesNotExist:
            store_stats.append({
                'id': store.id,
                'name': store.name,
                'views': 0,
                'offer_clicks': 0,  # Changed from coupon_clicks
                'offer_count': store.coupons.count(),  # Renamed from coupon_count
                'ctr': 0,
            })
    
    # Sort by views
    store_stats.sort(key=lambda x: x['views'], reverse=True)
    
    context = {
        'days': days,
        'store_stats': store_stats,
    }
    
    return render(request, 'analytics/store_analytics.html', context)

@login_required
@user_passes_test(is_admin_user)
def category_analytics(request):
    categories = Category.objects.all()
    
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    category_stats = []
    for category in categories:
        try:
            analytics = CategoryAnalytics.objects.get(category=category)
            stats = {
                'id': category.id,
                'name': category.name,
                'views': analytics.views,
                'offer_clicks': analytics.offer_clicks,  # Changed from coupon_clicks
                'offer_count': category.coupons.count(),  # Renamed from coupon_count
            }
            
            # Calculate click-through rate
            if stats['views'] > 0:
                stats['ctr'] = round((stats['offer_clicks'] / stats['views']) * 100, 2)  # Changed from coupon_clicks
            else:
                stats['ctr'] = 0
            
            category_stats.append(stats)
        except CategoryAnalytics.DoesNotExist:
            category_stats.append({
                'id': category.id,
                'name': category.name,
                'views': 0,
                'offer_clicks': 0,  # Changed from coupon_clicks
                'offer_count': category.coupons.count(),  # Renamed from coupon_count
                'ctr': 0,
            })
    
    # Sort by views
    category_stats.sort(key=lambda x: x['views'], reverse=True)
    
    context = {
        'days': days,
        'category_stats': category_stats,
    }
    
    return render(request, 'analytics/category_analytics.html', context)

@login_required
@user_passes_test(is_admin_user)
def user_analytics(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # User activity stats
    user_activity = UserActivity.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).values('user__username', 'user__id').annotate(
        activity_count=Count('id')
    ).order_by('-activity_count')
    
    # User session stats
    user_sessions = Session.objects.filter(
        start_time__gte=start_date,
        user__isnull=False
    ).values('user__username', 'user__id').annotate(
        session_count=Count('id'),
        total_duration=Sum(ExpressionWrapper(F('duration'), output_field=DurationField())),
        avg_duration=Avg(ExpressionWrapper(F('duration'), output_field=DurationField())),
        total_page_views=Sum('page_views')
    ).order_by('-session_count')
    
    context = {
        'days': days,
        'user_activity': user_activity,
        'user_sessions': user_sessions,
    }
    
    return render(request, 'analytics/user_analytics.html', context)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def track_event(request):
    if request.method == 'POST':
        try:
            # Parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid JSON: {str(e)}'
                }, status=400)
            
            # Validate required fields
            if not isinstance(data, dict):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid data format'
                }, status=400)
                
            event_type = data.get('event_type')
            page = data.get('page', '')
            element = data.get('element', '')
            event_data = data.get('data', {})
            
            # Make sure event_data is a dictionary
            if not isinstance(event_data, dict):
                event_data = {}
            
            # Get session ID
            session_id = getattr(request, 'analytics_session_id', '')
            
            # Create the event record
            Event.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=session_id,
                event_type=event_type,
                page=page,
                element=element,
                data=event_data
            )
            
            # Update specific analytics based on event type
            if event_type == 'copy_code':
                slug = event_data.get('slug')
                coupon_code = event_data.get('coupon_code')
                
                if slug:
                    try:
                        # Try to find coupon by ID
                        try:
                            import uuid
                            uuid.UUID(slug)
                            offer = Coupon.objects.get(slug=slug)
                        except (ValueError, TypeError):
                            # If not a valid UUID, try to find by code
                            offer = Coupon.objects.get(code=slug)
                        
                        if offer:
                            analytics, created = OfferAnalytics.objects.get_or_create(offer=offer)  # Changed from CouponAnalytics and coupon
                            analytics.increment_code_copies()
                    except Exception as e:
                        print(f"Error updating offer analytics: {e}")
            
            # Handle other event types
            elif event_type == 'save_offer':  # Changed from save_coupon
                slug = event_data.get('slug')
                if slug:
                    try:
                        # Try to find coupon by ID
                        try:
                            import uuid
                            uuid.UUID(slug)
                            offer = Coupon.objects.get(slug=slug)
                        except (ValueError, TypeError):
                            # If not a valid UUID, try to find by code
                            offer = Coupon.objects.get(code=slug)
                        
                        if offer:
                            analytics, created = OfferAnalytics.objects.get_or_create(offer=offer)  # Changed from CouponAnalytics and coupon
                            analytics.increment_saves()
                    except Exception as e:
                        print(f"Error updating offer analytics: {e}")
            
            elif event_type == 'use_offer':  # Changed from use_coupon
                slug = event_data.get('slug')
                if slug:
                    try:
                        # Try to find coupon by ID
                        try:
                            import uuid
                            uuid.UUID(slug)
                            offer = Coupon.objects.get(slug=slug)
                        except (ValueError, TypeError):
                            # If not a valid UUID, try to find by code
                            offer = Coupon.objects.get(code=slug)
                        
                        if offer:
                            analytics, created = OfferAnalytics.objects.get_or_create(offer=offer)  # Changed from CouponAnalytics and coupon
                            analytics.increment_uses()
                    except Exception as e:
                        print(f"Error updating offer analytics: {e}")
            
            return JsonResponse({'status': 'success'})
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)