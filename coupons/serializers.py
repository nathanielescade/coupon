from rest_framework import serializers
from .models import Coupon, CouponProvider, Store, Category, UserCoupon, CouponUsage
from django.contrib.auth.models import User

class CouponProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponProvider
        fields = '__all__'

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    provider = CouponProviderSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    is_expired = serializers.ReadOnlyField()
    discount_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = ('id', 'usage_count', 'created_by', 'created_at', 'updated_at')

class CouponCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = ('id', 'usage_count', 'created_by', 'created_at', 'updated_at')

class UserCouponSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    
    class Meta:
        model = UserCoupon
        fields = '__all__'

class CouponUsageSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = '__all__'