from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string

from django.db.models import Count, Sum, Avg, Q
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from coupons.models import (
    Coupon, Store, Category, UserOffer, OfferUsage, Newsletter, NewsletterSubscriber, 
    SEO, HomePageSEO, Tag, DealHighlight, DealSection
)
from analytics.models import PageView, Event, OfferAnalytics, StoreAnalytics, CategoryAnalytics
from .forms import (
    OfferForm, StoreForm, CategoryForm, UserForm, NewsletterForm, 
    TagForm, SEOForm, HomePageSEOForm, DealSectionForm, DealHighlightForm
)
import json

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# admin_panel/views.py (updated sections)

@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Basic stats - updated to use offers terminology
    total_offers = Coupon.objects.count()
    active_offers = Coupon.objects.filter(is_active=True).count()
    total_stores = Store.objects.count()
    total_users = User.objects.count()
    
    # Deal section stats
    special_offers = Coupon.objects.filter(is_special=True, is_active=True).count()
    amazon_deals = Coupon.objects.filter(source='AMAZON', is_active=True).count()
    hot_deals = Coupon.objects.filter(coupon_type='DEAL', is_active=True, is_special=False).count()
    coupon_codes = Coupon.objects.filter(coupon_type__in=['CODE', 'PRINTABLE', 'FREE_SHIPPING'], is_active=True).count()
    
    # Newsletter stats
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    recent_subscribers = NewsletterSubscriber.objects.order_by('-subscribed_at')[:5]
    recent_subscribers_count = NewsletterSubscriber.objects.filter(
        subscribed_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Recent activity
    recent_offers = Coupon.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Quick stats
    new_offers_last_7_days = Coupon.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    new_users_last_7_days = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    offer_usage_last_7_days = OfferUsage.objects.filter(
        used_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    context = {
        'days': days,
        'total_offers': total_offers,
        'active_offers': active_offers,
        'total_stores': total_stores,
        'total_users': total_users,
        'special_offers': special_offers,
        'amazon_deals': amazon_deals,
        'hot_deals': hot_deals,
        'coupon_codes': coupon_codes,
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'recent_subscribers': recent_subscribers,
        'recent_subscribers_count': recent_subscribers_count,
        'recent_offers': recent_offers,
        'recent_users': recent_users,
        'new_offers_last_7_days': new_offers_last_7_days,
        'new_users_last_7_days': new_users_last_7_days,
        'offer_usage_last_7_days': offer_usage_last_7_days,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# Add new views for deal sections
@login_required
@user_passes_test(is_staff_user)
def deal_section_list(request):
    sections = DealSection.objects.all()
    
    context = {
        'sections': sections,
    }
    
    return render(request, 'admin_panel/deal_section_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def deal_section_create(request):
    if request.method == 'POST':
        form = DealSectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deal section created successfully!')
            return redirect('admin_panel:deal_section_list')
    else:
        form = DealSectionForm()
    
    context = {
        'form': form,
        'title': 'Create Deal Section',
    }
    
    return render(request, 'admin_panel/deal_section_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def deal_highlight_list(request):
    highlights = DealHighlight.objects.all().order_by('section', 'display_order')
    
    context = {
        'highlights': highlights,
    }
    
    return render(request, 'admin_panel/deal_highlight_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def deal_highlight_create(request):
    if request.method == 'POST':
        form = DealHighlightForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deal highlight created successfully!')
            return redirect('admin_panel:deal_highlight_list')
    else:
        form = DealHighlightForm()
    
    context = {
        'form': form,
        'title': 'Create Deal Highlight',
    }
    
    return render(request, 'admin_panel/deal_highlight_form.html', context)




# admin_panel/views.py (add these views)

# Deal Section Management Views
@login_required
@user_passes_test(is_staff_user)
def deal_section_edit(request, section_id):
    section = get_object_or_404(DealSection, id=section_id)
    
    if request.method == 'POST':
        form = DealSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deal section updated successfully!')
            return redirect('admin_panel:deal_section_list')
    else:
        form = DealSectionForm(instance=section)
    
    context = {
        'form': form,
        'section': section,
        'title': 'Edit Deal Section',
    }
    
    return render(request, 'admin_panel/deal_section_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def deal_section_delete(request, section_id):
    section = get_object_or_404(DealSection, id=section_id)
    
    if request.method == 'POST':
        section.delete()
        messages.success(request, 'Deal section deleted successfully!')
        return redirect('admin_panel:deal_section_list')
    
    context = {
        'section': section,
    }
    
    return render(request, 'admin_panel/deal_section_delete.html', context)

# Deal Highlight Management Views
@login_required
@user_passes_test(is_staff_user)
def deal_highlight_edit(request, highlight_id):
    highlight = get_object_or_404(DealHighlight, id=highlight_id)
    
    if request.method == 'POST':
        form = DealHighlightForm(request.POST, instance=highlight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deal highlight updated successfully!')
            return redirect('admin_panel:deal_highlight_list')
    else:
        form = DealHighlightForm(instance=highlight)
    
    context = {
        'form': form,
        'highlight': highlight,
        'title': 'Edit Deal Highlight',
    }
    
    return render(request, 'admin_panel/deal_highlight_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def deal_highlight_delete(request, highlight_id):
    highlight = get_object_or_404(DealHighlight, id=highlight_id)
    
    if request.method == 'POST':
        highlight.delete()
        messages.success(request, 'Deal highlight deleted successfully!')
        return redirect('admin_panel:deal_highlight_list')
    
    context = {
        'highlight': highlight,
    }
    
    return render(request, 'admin_panel/deal_highlight_delete.html', context)

@login_required
@user_passes_test(is_staff_user)
def offer_list(request):
    offers = Coupon.objects.all().order_by('-created_at')
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        offers = offers.filter(is_active=True)
    elif active_filter == 'false':
        offers = offers.filter(is_active=False)
    
    # Filter by source
    source_filter = request.GET.get('source')
    if source_filter:
        offers = offers.filter(source=source_filter)
    
    # Filter by section
    section_filter = request.GET.get('section')
    if section_filter == 'special':
        offers = offers.filter(is_special=True)
    elif section_filter == 'amazon':
        offers = offers.filter(source='AMAZON')
    elif section_filter == 'coupons':
        offers = offers.filter(coupon_type__in=['CODE', 'PRINTABLE', 'FREE_SHIPPING'])
    elif section_filter == 'deals':
        offers = offers.filter(coupon_type='DEAL', is_special=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        offers = offers.filter(
            Q(title__icontains=search_query) | 
            Q(code__icontains=search_query) |
            Q(store__name__icontains=search_query)
        )
    
    context = {
        'offers': offers,
        'active_filter': active_filter,
        'source_filter': source_filter,
        'section_filter': section_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/offer_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def offer_create(request):
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.created_by = request.user
            offer.save()
            messages.success(request, 'Offer created successfully!')
            return redirect('admin_panel:offer_detail', slug=offer.slug)
    else:
        form = OfferForm()
    
    context = {
        'form': form,
        'title': 'Create Offer',
    }
    
    return render(request, 'admin_panel/offer_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def offer_edit(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('admin_panel:offer_detail', slug=offer.slug)
    else:
        form = OfferForm(instance=offer)
    
    context = {
        'form': form,
        'offer': offer,
        'title': 'Edit Offer',
    }
    
    return render(request, 'admin_panel/offer_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def offer_delete(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Offer deleted successfully!')
        return redirect('admin_panel:offer_list')
    
    context = {
        'offer': offer,
    }
    
    return render(request, 'admin_panel/offer_delete.html', context)

@login_required
@user_passes_test(is_staff_user)
def offer_detail(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    
    # Get analytics data if available
    try:
        analytics = OfferAnalytics.objects.get(offer=offer)
    except OfferAnalytics.DoesNotExist:
        analytics = None
    
    context = {
        'offer': offer,
        'analytics': analytics,
    }
    
    return render(request, 'admin_panel/offer_detail.html', context)

# Store management views
@login_required
@user_passes_test(is_staff_user)
def store_list(request):
    stores = Store.objects.all().order_by('name')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        stores = stores.filter(name__icontains=search_query)
    
    context = {
        'stores': stores,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/store_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def store_create(request):
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store created successfully!')
            return redirect('admin_panel:store_list')
    else:
        form = StoreForm()
    
    context = {
        'form': form,
        'title': 'Create Store',
    }
    
    return render(request, 'admin_panel/store_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def store_edit(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store updated successfully!')
            return redirect('admin_panel:store_list')
    else:
        form = StoreForm(instance=store)
    
    context = {
        'form': form,
        'store': store,
        'title': 'Edit Store',
    }
    
    return render(request, 'admin_panel/store_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def store_delete(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)
    
    if request.method == 'POST':
        store.delete()
        messages.success(request, 'Store deleted successfully!')
        return redirect('admin_panel:store_list')
    
    context = {
        'store': store,
    }
    
    return render(request, 'admin_panel/store_delete.html', context)

# Category management views
@login_required
@user_passes_test(is_staff_user)
def category_list(request):
    categories = Category.objects.all().order_by('name')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/category_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('admin_panel:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Create Category',
    }
    
    return render(request, 'admin_panel/category_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def category_edit(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('admin_panel:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category',
    }
    
    return render(request, 'admin_panel/category_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def category_delete(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('admin_panel:category_list')
    
    context = {
        'category': category,
    }
    
    return render(request, 'admin_panel/category_delete.html', context)

# Tag management views
@login_required
@user_passes_test(is_staff_user)
def tag_list(request):
    tags = Tag.objects.all().order_by('name')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        tags = tags.filter(name__icontains=search_query)
    
    context = {
        'tags': tags,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/tag_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully!')
            return redirect('admin_panel:tag_list')
    else:
        form = TagForm()
    
    context = {
        'form': form,
        'title': 'Create Tag',
    }
    
    return render(request, 'admin_panel/tag_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def tag_edit(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully!')
            return redirect('admin_panel:tag_list')
    else:
        form = TagForm(instance=tag)
    
    context = {
        'form': form,
        'tag': tag,
        'title': 'Edit Tag',
    }
    
    return render(request, 'admin_panel/tag_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully!')
        return redirect('admin_panel:tag_list')
    
    context = {
        'tag': tag,
    }
    
    return render(request, 'admin_panel/tag_delete.html', context)

# User management views
@login_required
@user_passes_test(is_staff_user)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter by staff status
    staff_filter = request.GET.get('staff')
    if staff_filter == 'true':
        users = users.filter(is_staff=True)
    elif staff_filter == 'false':
        users = users.filter(is_staff=False)
    
    context = {
        'users': users,
        'search_query': search_query,
        'staff_filter': staff_filter,
    }
    
    return render(request, 'admin_panel/user_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('admin_panel:user_list')
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': 'Edit User',
    }
    
    return render(request, 'admin_panel/user_form.html', context)

# Analytics view
@login_required
@user_passes_test(is_staff_user)
def analytics_view(request):
    # Redirect to the existing analytics dashboard
    return redirect('analytics:dashboard')

# Newsletter management views
@login_required
@user_passes_test(is_staff_user)
def newsletter_list(request):
    newsletters = Newsletter.objects.all().order_by('-created_at')
    
    context = {
        'newsletters': newsletters,
    }
    
    return render(request, 'admin_panel/newsletter_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def newsletter_create(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save()
            messages.success(request, 'Newsletter created successfully!')
            return redirect('admin_panel:newsletter_edit', newsletter_id=newsletter.id)
    else:
        form = NewsletterForm()
    
    context = {
        'form': form,
        'title': 'Create Newsletter',
    }
    
    return render(request, 'admin_panel/newsletter_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def newsletter_edit(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.method == 'POST':
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, 'Newsletter updated successfully!')
            return redirect('admin_panel:newsletter_list')
    else:
        form = NewsletterForm(instance=newsletter)
    
    context = {
        'form': form,
        'newsletter': newsletter,
        'title': 'Edit Newsletter',
    }
    
    return render(request, 'admin_panel/newsletter_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def newsletter_delete(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if request.method == 'POST':
        newsletter.delete()
        messages.success(request, 'Newsletter deleted successfully!')
        return redirect('admin_panel:newsletter_list')
    
    context = {
        'newsletter': newsletter,
    }
    
    return render(request, 'admin_panel/newsletter_delete.html', context)

@login_required
@user_passes_test(is_staff_user)
def newsletter_send(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    if newsletter.is_sent:
        messages.warning(request, f'Newsletter "{newsletter.subject}" was already sent on {newsletter.sent_at}')
        return redirect('admin_panel:newsletter_list')
    
    if request.method == 'POST':
        success, message = newsletter.send_newsletter()
        if success:
            messages.success(request, f'Newsletter sent successfully. {message}')
        else:
            messages.error(request, f'Failed to send newsletter: {message}')
        return redirect('admin_panel:newsletter_list')
    
    context = {
        'newsletter': newsletter,
        'subscriber_count': NewsletterSubscriber.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'admin_panel/newsletter_send.html', context)

@login_required
@user_passes_test(is_staff_user)
def newsletter_preview(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    
    # Get latest offers for the preview
    days_ago = 7
    start_date = timezone.now() - timedelta(days=days_ago)
    offers = Coupon.objects.filter(
        is_active=True,
        created_at__gte=start_date
    ).order_by('-created_at')[:10]
    
    context = {
        'subject': newsletter.subject,
        'content': newsletter.content,
        'offers': offers,
        'email': 'subscriber@example.com'  # Example email for preview
    }
    
    return render(request, 'custom_newsletter_email.html', context)

@login_required
@user_passes_test(is_staff_user)
def subscriber_list(request):
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        subscribers = subscribers.filter(is_active=True)
    elif active_filter == 'false':
        subscribers = subscribers.filter(is_active=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        subscribers = subscribers.filter(email__icontains=search_query)
    
    context = {
        'subscribers': subscribers,
        'active_filter': active_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/subscriber_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def export_subscribers(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Subscribed At', 'Status'])
    
    subscribers = NewsletterSubscriber.objects.all().order_by('-subscribed_at')
    for subscriber in subscribers:
        writer.writerow([
            subscriber.email,
            subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Active' if subscriber.is_active else 'Inactive'
        ])
    
    return response

# SEO Management Views
@login_required
@user_passes_test(is_staff_user)
def seo_list(request):
    seo_objects = SEO.objects.all().order_by('content_type', 'content_id')
    
    # Filter by content type
    content_type_filter = request.GET.get('content_type')
    if content_type_filter:
        seo_objects = seo_objects.filter(content_type=content_type_filter)
    
    context = {
        'seo_objects': seo_objects,
        'content_type_filter': content_type_filter,
        'content_types': SEO.CONTENT_TYPES,
    }
    
    return render(request, 'admin_panel/seo_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def seo_edit(request, seo_id):
    seo = get_object_or_404(SEO, id=seo_id)
    
    if request.method == 'POST':
        # Add request.FILES to handle image uploads
        form = SEOForm(request.POST, request.FILES, instance=seo)
        if form.is_valid():
            form.save()
            messages.success(request, 'SEO metadata updated successfully!')
            return redirect('admin_panel:seo_list')
    else:
        form = SEOForm(instance=seo)
    
    context = {
        'form': form,
        'seo': seo,
        'title': f'Edit SEO: {seo.get_content_type_display()} - {seo.content_id}',
    }
    
    return render(request, 'admin_panel/seo_form.html', context)





@login_required
@user_passes_test(is_staff_user)
def seo_create_for_offer(request, slug):
    offer = get_object_or_404(Coupon, slug=slug)
    
    # Check if SEO already exists
    if hasattr(offer, 'seo') and offer.seo:
        messages.warning(request, 'SEO metadata already exists for this offer.')
        return redirect('admin_panel:seo_edit', seo_id=offer.seo.id)
    
    if request.method == 'POST':
        # Add request.FILES to handle image uploads
        form = SEOForm(request.POST, request.FILES)
        if form.is_valid():
            seo = form.save(commit=False)
            seo.content_type = 'offer'
            seo.content_id = str(offer.slug)
            seo.save()
            
            # Link to offer
            offer.seo = seo
            offer.save()
            
            messages.success(request, 'SEO metadata created successfully!')
            return redirect('admin_panel:offer_detail', slug=offer.slug)
    else:
        form = SEOForm(initial={
            'meta_title': f"{offer.title} - {offer.discount_display} | {offer.store.name} Offer",
            'meta_description': f"Get {offer.discount_display} at {offer.store.name}. {offer.description[:100]}...",
            'meta_keywords': f"{offer.store.name}, {offer.category.name}, {offer.title}, offer, promo code, discount",
        })
    
    context = {
        'form': form,
        'offer': offer,
        'title': f'Create SEO for Offer: {offer.title}',
    }
    
    return render(request, 'admin_panel/seo_form.html', context)




@login_required
@user_passes_test(is_staff_user)
def seo_create_for_store(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug)
    
    # Check if SEO already exists
    if hasattr(store, 'seo') and store.seo:
        messages.warning(request, 'SEO metadata already exists for this store.')
        return redirect('admin_panel:seo_edit', seo_id=store.seo.id)
    
    if request.method == 'POST':
        # Add request.FILES to handle image uploads
        form = SEOForm(request.POST, request.FILES)
        if form.is_valid():
            seo = form.save(commit=False)
            seo.content_type = 'store'
            seo.content_id = store.slug
            seo.save()
            
            # Link to store
            store.seo = seo
            store.save()
            
            messages.success(request, 'SEO metadata created successfully!')
            return redirect('admin_panel:store_list')
    else:
        form = SEOForm(initial={
            'meta_title': f"{store.name} Offers & Promo Codes - Save Money Today",
            'meta_description': f"Find the latest {store.name} offers, promo codes and deals. Save money with verified {store.name} discount codes and offers.",
            'meta_keywords': f"{store.name}, offers, promo codes, deals, discounts, savings",
        })
    
    context = {
        'form': form,
        'store': store,
        'title': f'Create SEO for Store: {store.name}',
    }
    
    return render(request, 'admin_panel/seo_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def seo_create_for_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    # Check if SEO already exists
    if hasattr(category, 'seo') and category.seo:
        messages.warning(request, 'SEO metadata already exists for this category.')
        return redirect('admin_panel:seo_edit', seo_id=category.seo.id)
    
    if request.method == 'POST':
        # Add request.FILES to handle image uploads
        form = SEOForm(request.POST, request.FILES)
        if form.is_valid():
            seo = form.save(commit=False)
            seo.content_type = 'category'
            seo.content_id = category.slug
            seo.save()
            
            # Link to category
            category.seo = seo
            category.save()
            
            messages.success(request, 'SEO metadata created successfully!')
            return redirect('admin_panel:category_list')
    else:
        form = SEOForm(initial={
            'meta_title': f"{category.name} Offers & Deals - Best Discounts",
            'meta_description': f"Browse {category.name} offers and deals from top brands. Save money with verified {category.name} discount codes.",
            'meta_keywords': f"{category.name}, offers, deals, discounts, savings, promo codes",
        })
    
    context = {
        'form': form,
        'category': category,
        'title': f'Create SEO for Category: {category.name}',
    }
    
    return render(request, 'admin_panel/seo_form.html', context)





@login_required
@user_passes_test(is_staff_user)
def homepage_seo(request):
    try:
        homepage_seo = HomePageSEO.objects.get()
    except HomePageSEO.DoesNotExist:
        homepage_seo = HomePageSEO()
    
    if request.method == 'POST':
        # Add request.FILES to handle image uploads
        form = HomePageSEOForm(request.POST, request.FILES, instance=homepage_seo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Homepage SEO settings updated successfully!')
            return redirect('admin_panel:homepage_seo')
    else:
        form = HomePageSEOForm(instance=homepage_seo)
    
    context = {
        'form': form,
        'title': 'Homepage SEO Settings',
    }
    
    return render(request, 'admin_panel/homepage_seo.html', context)