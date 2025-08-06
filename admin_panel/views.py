from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q
from django.urls import reverse
from django.contrib import messages
from coupons.models import Coupon, Store, Category, UserCoupon, CouponUsage
from analytics.models import PageView, Event, CouponAnalytics, StoreAnalytics, CategoryAnalytics
from .forms import CouponForm, StoreForm, CategoryForm, UserForm
import json

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# Keep all your existing views here...

@login_required
@user_passes_test(is_staff_user)
def dashboard(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Basic stats
    total_coupons = Coupon.objects.count()
    active_coupons = Coupon.objects.filter(is_active=True).count()
    total_stores = Store.objects.count()
    total_users = User.objects.count()
    
    # Newsletter stats
    from coupons.models import NewsletterSubscriber
    total_subscribers = NewsletterSubscriber.objects.count()
    active_subscribers = NewsletterSubscriber.objects.filter(is_active=True).count()
    recent_subscribers = NewsletterSubscriber.objects.order_by('-subscribed_at')[:5]
    recent_subscribers_count = NewsletterSubscriber.objects.filter(
        subscribed_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Recent activity
    recent_coupons = Coupon.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Quick stats
    new_coupons_last_7_days = Coupon.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    new_users_last_7_days = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    coupon_usage_last_7_days = CouponUsage.objects.filter(
        used_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    context = {
        'days': days,
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'total_stores': total_stores,
        'total_users': total_users,
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'recent_subscribers': recent_subscribers,
        'recent_subscribers_count': recent_subscribers_count,
        'recent_coupons': recent_coupons,
        'recent_users': recent_users,
        'new_coupons_last_7_days': new_coupons_last_7_days,
        'new_users_last_7_days': new_users_last_7_days,
        'coupon_usage_last_7_days': coupon_usage_last_7_days,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)





@login_required
@user_passes_test(is_staff_user)
def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    
    # Filter by active status
    active_filter = request.GET.get('active')
    if active_filter == 'true':
        coupons = coupons.filter(is_active=True)
    elif active_filter == 'false':
        coupons = coupons.filter(is_active=False)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        coupons = coupons.filter(
            Q(title__icontains=search_query) | 
            Q(code__icontains=search_query) |
            Q(store__name__icontains=search_query)
        )
    
    context = {
        'coupons': coupons,
        'active_filter': active_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/coupon_list.html', context)

@login_required
@user_passes_test(is_staff_user)
def coupon_create(request):
    if request.method == 'POST':
        form = CouponForm(request.POST, request.FILES)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.created_by = request.user
            coupon.save()
            messages.success(request, 'Coupon created successfully!')
            return redirect('admin_panel:coupon_detail', coupon_id=coupon.id)
    else:
        form = CouponForm()
    
    context = {
        'form': form,
        'title': 'Create Coupon',
    }
    
    return render(request, 'admin_panel/coupon_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def coupon_edit(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, request.FILES, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon updated successfully!')
            return redirect('admin_panel:coupon_detail', coupon_id=coupon.id)
    else:
        form = CouponForm(instance=coupon)
    
    context = {
        'form': form,
        'coupon': coupon,
        'title': 'Edit Coupon',
    }
    
    return render(request, 'admin_panel/coupon_form.html', context)

@login_required
@user_passes_test(is_staff_user)
def coupon_delete(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, 'Coupon deleted successfully!')
        return redirect('admin_panel:coupon_list')
    
    context = {
        'coupon': coupon,
    }
    
    return render(request, 'admin_panel/coupon_delete.html', context)

@login_required
@user_passes_test(is_staff_user)
def coupon_detail(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    # Get analytics data if available
    try:
        analytics = CouponAnalytics.objects.get(coupon=coupon)
    except CouponAnalytics.DoesNotExist:
        analytics = None
    
    context = {
        'coupon': coupon,
        'analytics': analytics,
    }
    
    return render(request, 'admin_panel/coupon_detail.html', context)


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
















from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from coupons.models import Coupon, Store, Category, UserCoupon, CouponUsage, Newsletter, NewsletterSubscriber
from analytics.models import PageView, Event, CouponAnalytics, StoreAnalytics, CategoryAnalytics
from .forms import CouponForm, StoreForm, CategoryForm, UserForm, NewsletterForm
import json

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# ... keep all your existing views ...

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
    
    # Get latest coupons for the preview
    days_ago = 7
    start_date = timezone.now() - timedelta(days=days_ago)
    coupons = Coupon.objects.filter(
        is_active=True,
        created_at__gte=start_date
    ).order_by('-created_at')[:10]
    
    context = {
        'subject': newsletter.subject,
        'content': newsletter.content,
        'coupons': coupons,
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









from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404
from coupons.models import SEO, HomePageSEO, Coupon, Store, Category
from .forms import SEOForm, HomePageSEOForm

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# Keep all your existing views here...

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
        form = SEOForm(request.POST, instance=seo)
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
def seo_create_for_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    # Check if SEO already exists
    if hasattr(coupon, 'seo') and coupon.seo:
        messages.warning(request, 'SEO metadata already exists for this coupon.')
        return redirect('admin_panel:seo_edit', seo_id=coupon.seo.id)
    
    if request.method == 'POST':
        form = SEOForm(request.POST)
        if form.is_valid():
            seo = form.save(commit=False)
            seo.content_type = 'coupon'
            seo.content_id = str(coupon.id)
            seo.save()
            
            # Link to coupon
            coupon.seo = seo
            coupon.save()
            
            messages.success(request, 'SEO metadata created successfully!')
            return redirect('admin_panel:coupon_detail', coupon_id=coupon.id)
    else:
        form = SEOForm(initial={
            'meta_title': f"{coupon.title} - {coupon.discount_display} | {coupon.store.name} Coupon",
            'meta_description': f"Get {coupon.discount_display} at {coupon.store.name}. {coupon.description[:100]}...",
            'meta_keywords': f"{coupon.store.name}, {coupon.category.name}, {coupon.title}, coupon, promo code, discount",
        })
    
    context = {
        'form': form,
        'coupon': coupon,
        'title': f'Create SEO for Coupon: {coupon.title}',
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
        form = SEOForm(request.POST)
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
            'meta_title': f"{store.name} Coupons & Promo Codes - Save Money Today",
            'meta_description': f"Find the latest {store.name} coupons, promo codes and deals. Save money with verified {store.name} discount codes and offers.",
            'meta_keywords': f"{store.name}, coupons, promo codes, deals, discounts, savings",
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
        form = SEOForm(request.POST)
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
            'meta_title': f"{category.name} Coupons & Deals - Best Discounts",
            'meta_description': f"Browse {category.name} coupons and deals from top brands. Save money with verified {category.name} discount codes.",
            'meta_keywords': f"{category.name}, coupons, deals, discounts, savings, promo codes",
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
        form = HomePageSEOForm(request.POST, instance=homepage_seo)
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