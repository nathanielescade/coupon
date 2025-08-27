from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from . import views
from .sitemaps import OfferSitemap, StoreSitemap, CategorySitemap, StaticViewSitemap

router = DefaultRouter()
router.register(r'offers', views.OfferViewSet)
router.register(r'providers', views.CouponProviderViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'categories', views.CategoryViewSet)

# Sitemaps
sitemaps = {
    'offers': OfferSitemap,
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # Frontend URLs
    path('', views.HomeView.as_view(), name='home'),
    
    # Offer URLs - new structure
    path('deals/<slug:section>/', views.deal_section, name='deal_section'),
    path('deals/<slug:section>/<slug:slug>/', views.deal_detail, name='deal_detail'),
    
    # Legacy redirect for old coupon URLs
    path('coupon/<slug:slug>/', views.legacy_coupon_redirect, name='legacy_coupon_redirect'),
    
    # Offer management
    path('offer/new/', views.OfferCreateView.as_view(), name='offer_create'),
    path('offer/<slug:slug>/edit/', views.OfferUpdateView.as_view(), name='offer_update'),
    path('offer/<slug:slug>/delete/', views.OfferDeleteView.as_view(), name='offer_delete'),
    
    # Store and Category URLs
    path('store/<slug:store_slug>/', views.StoreDetailView.as_view(), name='store_detail'),
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Search
    path('search/', views.SearchView.as_view(), name='search'),
    
    # User URLs
    path('my-offers/', views.my_offers, name='my_offers'),
    path('save/<slug:slug>/', views.save_offer, name='save_offer'),
    path('use/<slug:slug>/', views.use_offer, name='use_offer'),
    
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(http_method_names=['get', 'post'], next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
    
    # All Offers Pages
    path('offers/', views.AllOffersView.as_view(), name='all_offers'),
    path('offers/featured/', views.FeaturedOffersView.as_view(), name='featured_offers'),
    path('offers/expiring/', views.ExpiringOffersView.as_view(), name='expiring_offers'),
    path('offers/latest/', views.LatestOffersView.as_view(), name='latest_offers'),
    
    # All Stores and Categories Pages
    path('stores/', views.AllStoresView.as_view(), name='all_stores'),
    path('categories/', views.AllCategoriesView.as_view(), name='all_categories'),
    
    # AJAX filtering
    path('filter-offers/', views.filter_offers_ajax, name='filter_offers_ajax'),
    
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