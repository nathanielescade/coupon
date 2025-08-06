from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<uuid:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<uuid:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/<uuid:coupon_id>/detail/', views.coupon_detail, name='coupon_detail'),
    path('stores/', views.store_list, name='store_list'),
    path('stores/create/', views.store_create, name='store_create'),
    path('stores/<slug:store_slug>/edit/', views.store_edit, name='store_edit'),
    path('stores/<slug:store_slug>/delete/', views.store_delete, name='store_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<slug:category_slug>/edit/', views.category_edit, name='category_edit'),
    path('categories/<slug:category_slug>/delete/', views.category_delete, name='category_delete'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('analytics/', views.analytics_view, name='analytics'),


    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/create/', views.newsletter_create, name='newsletter_create'),
    path('newsletters/<int:newsletter_id>/edit/', views.newsletter_edit, name='newsletter_edit'),
    path('newsletters/<int:newsletter_id>/delete/', views.newsletter_delete, name='newsletter_delete'),
    path('newsletters/<int:newsletter_id>/send/', views.newsletter_send, name='newsletter_send'),
    path('newsletters/<int:newsletter_id>/preview/', views.newsletter_preview, name='newsletter_preview'),
    path('subscribers/export/', views.export_subscribers, name='export_subscribers'),
    # Newsletter subscribers
    path('subscribers/', views.subscriber_list, name='subscriber_list'),
    
    path('seo/', views.seo_list, name='seo_list'),
    path('seo/<int:seo_id>/edit/', views.seo_edit, name='seo_edit'),
    path('seo/coupon/<uuid:coupon_id>/create/', views.seo_create_for_coupon, name='seo_create_for_coupon'),
    path('seo/store/<slug:store_slug>/create/', views.seo_create_for_store, name='seo_create_for_store'),
    path('seo/category/<slug:category_slug>/create/', views.seo_create_for_category, name='seo_create_for_category'),
    path('seo/homepage/', views.homepage_seo, name='homepage_seo'),
    
]