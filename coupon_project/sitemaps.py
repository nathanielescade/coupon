from django.contrib.sitemaps import views as sitemap_views
from coupons.sitemaps import (
    CouponSitemap, StoreSitemap, CategorySitemap, StaticViewSitemap,
    FeaturedCouponsSitemap, ExpiringCouponsSitemap
)

sitemaps = {
    'coupons': CouponSitemap,
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
    'featured': FeaturedCouponsSitemap,
    'expiring': ExpiringCouponsSitemap,
}