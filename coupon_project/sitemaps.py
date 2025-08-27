from django.contrib.sitemaps import views as sitemap_views
from coupons.sitemaps import (
    OfferSitemap, StoreSitemap, CategorySitemap, StaticViewSitemap,
    FeaturedOffersSitemap, ExpiringOffersSitemap
)

sitemaps = {
    'offers': OfferSitemap,  # Updated from 'coupons'
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
    'featured': FeaturedOffersSitemap,
    'expiring': ExpiringOffersSitemap,
}