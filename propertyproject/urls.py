from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include   # 👈 idhu important
from property import views


urlpatterns = [
    path('', include('property.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)