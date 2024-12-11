
from django.contrib import admin
from django.urls import path , include 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('', include('accounts.urls')),
    path('status/', include('status.urls')),
    path('rest-auth/', include('dj_rest_auth.urls')),
    path('rest-auth/registration/',include('dj_rest_auth.registration.urls')),
]
