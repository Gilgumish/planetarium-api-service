from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from planetarium_service import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/planetarium/', include('planetarium.urls', namespace='planetarium')),
    path("api/user/", include("user.urls", namespace="user")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
