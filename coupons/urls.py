from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import CouponSitemap, StoreSitemap, CategorySitemap, StaticViewSitemap

router = DefaultRouter()
router.register(r'coupons', views.CouponViewSet)
router.register(r'providers', views.CouponProviderViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'categories', views.CategoryViewSet)

# Sitemaps
sitemaps = {
    'coupons': CouponSitemap,
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # Frontend URLs
    path('', views.HomeView.as_view(), name='home'),
    
    # Coupon URLs - more specific patterns first
    path('coupon/new/', views.CouponCreateView.as_view(), name='coupon_create'),
    path('coupon/<slug:slug>/', views.CouponDetailView.as_view(), name='coupon_detail'),
    path('coupon/<slug:slug>/edit/', views.CouponUpdateView.as_view(), name='coupon_update'),
    path('coupon/<slug:slug>/delete/', views.CouponDeleteView.as_view(), name='coupon_delete'),
    
    path('store/<slug:store_slug>/', views.StoreDetailView.as_view(), name='store_detail'),
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('my-coupons/', views.my_coupons, name='my_coupons'),
    path('save/<slug:slug>/', views.save_coupon, name='save_coupon'),
    path('use/<slug:slug>/', views.use_coupon, name='use_coupon'),
    
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(http_method_names=['get', 'post'], next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
    
    # All Coupons Pages
    path('coupons/', views.AllCouponsView.as_view(), name='all_coupons'),
    path('coupons/featured/', views.FeaturedCouponsView.as_view(), name='featured_coupons'),
    path('coupons/expiring/', views.ExpiringCouponsView.as_view(), name='expiring_coupons'),
    path('coupons/latest/', views.LatestCouponsView.as_view(), name='latest_coupons'),
    
    # All Stores and Categories Pages
    path('stores/', views.AllStoresView.as_view(), name='all_stores'),
    path('categories/', views.AllCategoriesView.as_view(), name='all_categories'),
    
    # Add this to your urlpatterns
    path('filter-coupons/', views.filter_coupons_ajax, name='filter_coupons_ajax'),

    # Newsletter management
    path('admin/newsletters/', views.newsletter_management, name='newsletter_management'),
    path('admin/newsletters/send/<int:newsletter_id>/', views.send_newsletter, name='send_newsletter'),
    path('admin/newsletters/preview/<int:newsletter_id>/', views.preview_newsletter, name='preview_newsletter'),
    
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    
    # Static pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # API URLs
    path('api/', include(router.urls)),
]