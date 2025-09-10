# project/sitemaps.py
from coupons.sitemaps import (
    OfferSitemap, StoreSitemap, CategorySitemap, StaticViewSitemap,
    FeaturedOffersSitemap, ExpiringOffersSitemap, DealSectionSitemap,
    TagSitemap, UserSitemap, StorePageSitemap, CategoryPageSitemap
)

sitemaps = {
    'offers': OfferSitemap,
    'stores': StoreSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
    'featured': FeaturedOffersSitemap,
    'expiring': ExpiringOffersSitemap,
    'sections': DealSectionSitemap,
    'tags': TagSitemap,
    'users': UserSitemap,
    'store_pages': StorePageSitemap,
    'category_pages': CategoryPageSitemap,
}