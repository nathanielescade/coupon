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
]