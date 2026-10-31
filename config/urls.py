from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .spa import spa_index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

# Everything else is handled by the Vue router.
urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/).*$", spa_index)]
