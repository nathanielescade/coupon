from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps import views as sitemap_views
from django.views.generic import TemplateView
from .sitemaps import sitemaps

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("coupons.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("analytics/", include("analytics.urls")),
    path("admin-panel/", include("admin_panel.urls")),

    # robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),

    # Sitemap Index + Sections
    path(
        "sitemap.xml",
        sitemap_views.index,
        {"sitemaps": sitemaps},
        name="sitemap_index",
    ),
    path(
        "sitemap-<section>.xml",
        sitemap_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
