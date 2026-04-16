from django.contrib import admin 
from django.urls import path, include  
from django.conf import settings        
from django.conf.urls.static import static 

from .views import (
    LoginView, 
    RegisterView, 
    capturar_datos_view, 
    telemetria_proxy_view,
    listar_capturas_view  
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/clima/', telemetria_proxy_view, name='telemetria_proxy'),
    path('api/vectores/capturar/', capturar_datos_view, name='capturar_datos'),
    path('api/vectores/listar/', listar_capturas_view, name='listar_capturas'),
    
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),

 
    path('api/ia/', include('analisis_vectores.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    