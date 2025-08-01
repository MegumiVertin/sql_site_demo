from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views    

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),       
    path("api/translate/", core_views.translate),
    path("api/progress/<uuid:job_id>/", core_views.progress),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
