from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.analytics_dashboard, name='dashboard'),
    path('offers/', views.offer_analytics, name='offer_analytics'),  # Changed from coupon_analytics
    path('stores/', views.store_analytics, name='store_analytics'),
    path('categories/', views.category_analytics, name='category_analytics'),
    path('users/', views.user_analytics, name='user_analytics'),
    path('track-event/', views.track_event, name='track_event'),
]