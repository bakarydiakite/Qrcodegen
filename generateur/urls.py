
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('cryptage.api_urls', namespace='api')),
    
    # Web interface
    path('', include('cryptage.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
