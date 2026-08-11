from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('movie.urls')),
    
    # /auth/login/, /auth/logout/ 등 URL 포함
    path('auth/', include('dj_rest_auth.urls')),
    
    # /auth/registration/ URL 포함
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
]




