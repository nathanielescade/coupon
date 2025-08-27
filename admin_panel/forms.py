# admin_panel/forms.py (updated)
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from coupons.models import Coupon, Store, Category, UserOffer, OfferUsage, NewsletterSubscriber, Newsletter, SEO, HomePageSEO, Tag, DealSection, DealHighlight

class OfferForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'title', 'description', 'code', 'coupon_type', 'discount_type',
            'discount_value', 'minimum_purchase', 'start_date', 'expiry_date',
            'is_active', 'is_featured', 'is_verified', 'is_special', 'is_popular',
            'usage_limit', 'terms_and_conditions', 'affiliate_link', 'store', 'category',
            'source', 'tags'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 4}),
            'tags': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'slug', 'website', 'logo', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class UserForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'shadow appearance-none rounded w-full py-2 px-3 bg-black/30 border border-blue-600 text-blue-100 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 10
            }),
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'slug']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class SEOForm(forms.ModelForm):
    class Meta:
        model = SEO
        fields = [
            'meta_title', 'meta_description', 'meta_keywords',
            'og_title', 'og_description', 'og_image', 'og_image_upload',
            'twitter_title', 'twitter_description', 'twitter_image', 'twitter_image_upload',
            'canonical_url', 'no_index', 'no_follow'
        ]
        widgets = {
            'meta_title': forms.TextInput(attrs={'class': 'form-input'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-input'}),
            'og_title': forms.TextInput(attrs={'class': 'form-input'}),
            'og_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'og_image': forms.URLInput(attrs={'class': 'form-input'}),
            'twitter_title': forms.TextInput(attrs={'class': 'form-input'}),
            'twitter_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'twitter_image': forms.URLInput(attrs={'class': 'form-input'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to file fields
        if 'og_image_upload' in self.fields:
            self.fields['og_image_upload'].widget.attrs['class'] = 'form-input'
        if 'twitter_image_upload' in self.fields:
            self.fields['twitter_image_upload'].widget.attrs['class'] = 'form-input'

class HomePageSEOForm(forms.ModelForm):
    class Meta:
        model = HomePageSEO
        fields = [
            'meta_title', 'meta_description', 'meta_keywords',
            'og_title', 'og_description', 'og_image', 'og_image_upload',
            'twitter_title', 'twitter_description', 'twitter_image', 'twitter_image_upload',
            'canonical_url', 'no_index', 'no_follow',
            'hero_title', 'hero_description'
        ]
        widgets = {
            'meta_title': forms.TextInput(attrs={'class': 'form-input'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-input'}),
            'og_title': forms.TextInput(attrs={'class': 'form-input'}),
            'og_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'og_image': forms.URLInput(attrs={'class': 'form-input'}),
            'twitter_title': forms.TextInput(attrs={'class': 'form-input'}),
            'twitter_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'twitter_image': forms.URLInput(attrs={'class': 'form-input'}),
            'canonical_url': forms.URLInput(attrs={'class': 'form-input'}),
            'hero_title': forms.TextInput(attrs={'class': 'form-input'}),
            'hero_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to file fields
        if 'og_image_upload' in self.fields:
            self.fields['og_image_upload'].widget.attrs['class'] = 'form-input'
        if 'twitter_image_upload' in self.fields:
            self.fields['twitter_image_upload'].widget.attrs['class'] = 'form-input'

# New forms for deal sections
class DealSectionForm(forms.ModelForm):
    class Meta:
        model = DealSection
        fields = ['name', 'slug', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'

class DealHighlightForm(forms.ModelForm):
    class Meta:
        model = DealHighlight
        fields = ['deal', 'section', 'display_order', 'is_active']
        widgets = {
            'display_order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to all fields
        for field_name, field in self.fields.items():
            if field.widget.__class__ in [forms.CheckboxInput, forms.RadioSelect]:
                field.widget.attrs['class'] = 'form-checkbox'
            else:
                field.widget.attrs['class'] = 'form-input'