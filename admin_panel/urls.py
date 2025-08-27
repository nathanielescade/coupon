# admin_panel/urls.py (updated)
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Offer management
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/create/', views.offer_create, name='offer_create'),
    path('offers/<slug:slug>/', views.offer_detail, name='offer_detail'),
    path('offers/<slug:slug>/edit/', views.offer_edit, name='offer_edit'),
    path('offers/<slug:slug>/delete/', views.offer_delete, name='offer_delete'),
    
    # Store management
    path('stores/', views.store_list, name='store_list'),
    path('stores/create/', views.store_create, name='store_create'),
    path('stores/<slug:store_slug>/', views.store_edit, name='store_edit'),
    path('stores/<slug:store_slug>/delete/', views.store_delete, name='store_delete'),
    
    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:category_slug>/', views.category_edit, name='category_edit'),
    path('categories/<slug:category_slug>/delete/', views.category_delete, name='category_delete'),
    
    # Tag management
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_edit, name='user_edit'),
    
    # Newsletter management
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='newsletter_create'),
    path('newsletters/<int:newsletter_id>/', views.newsletter_edit, name='newsletter_edit'),
    path('newsletters/<int:newsletter_id>/delete/', views.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<int:newsletter_id>/send/', views.newsletter_send, name='newsletter_send'),
    path('newsletters/<int:newsletter_id>/preview/', views.newsletter_preview, name='newsletter_preview'),
    
    # Subscriber management
    path('subscribers/', views.subscriber_list, name='subscriber_list'),
    path('subscribers/export/', views.export_subscribers, name='export_subscribers'),
    
    # SEO management
    path('seo/', views.seo_list, name='seo_list'),
    path('seo/<int:seo_id>/', views.seo_edit, name='seo_edit'),
    path('seo/offer/<slug:slug>/', views.seo_create_for_offer, name='seo_create_for_offer'),
    path('seo/store/<slug:store_slug>/', views.seo_create_for_store, name='seo_create_for_store'),
    path('seo/category/<slug:category_slug>/', views.seo_create_for_category, name='seo_create_for_category'),
    path('homepage-seo/', views.homepage_seo, name='homepage_seo'),
    
    # Deal Section management
    path('deal-sections/', views.deal_section_list, name='deal_section_list'),
    path('deal-sections/create/', views.deal_section_create, name='deal_section_create'),
    path('deal-sections/<int:section_id>/', views.deal_section_edit, name='deal_section_edit'),
    path('deal-sections/<int:section_id>/delete/', views.deal_section_delete, name='deal_section_delete'),
    
    # Deal Highlight management
    path('deal-highlights/', views.deal_highlight_list, name='deal_highlight_list'),
    path('deal-highlights/create/', views.deal_highlight_create, name='deal_highlight_create'),
    path('deal-highlights/<int:highlight_id>/', views.deal_highlight_edit, name='deal_highlight_edit'),
    path('deal-highlights/<int:highlight_id>/delete/', views.deal_highlight_delete, name='deal_highlight_delete'),
    
    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),
]