from rest_framework import serializers
from .models import (
    Coupon, CouponProvider, Store, Category, UserOffer, OfferUsage, 
    NewsletterSubscriber, Newsletter, SEO, HomePageSEO, Tag
)
from django.contrib.auth.models import User

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

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

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

# Renamed to match what views.py expects
class OfferSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    provider = CouponProviderSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    discount_display = serializers.ReadOnlyField()
    section = serializers.ReadOnlyField()
    
    class Meta:
        model = Coupon  # Still using the Coupon model
        fields = '__all__'
        read_only_fields = ('id', 'usage_count', 'created_by', 'created_at', 'updated_at', 'slug')

# Renamed to match what views.py expects
class OfferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon  # Still using the Coupon model
        fields = '__all__'
        read_only_fields = ('id', 'usage_count', 'created_by', 'created_at', 'updated_at', 'slug')

class UserOfferSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    offer = OfferSerializer(read_only=True)  # Using OfferSerializer here
    
    class Meta:
        model = UserOffer
        fields = '__all__'

class OfferUsageSerializer(serializers.ModelSerializer):
    offer = OfferSerializer(read_only=True)  # Using OfferSerializer here
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = OfferUsage
        fields = '__all__'

class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = '__all__'

class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = '__all__'
        read_only_fields = ('created_at', 'sent_at', 'is_sent')

class SEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = SEO
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class HomePageSEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePageSEO
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')