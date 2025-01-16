
from django.contrib import admin
from django.urls import path , include 
from dj_rest_auth import urls as dj_rest_auth_urls
from accounts.views import CustomRegisterView, CustomLoginView, CustomLogoutView

urlpatterns = [
    path('api/v1/admin/', admin.site.urls),
    path('api/v1/', include('chat.urls')),
    path('api/v1/accounts', include('accounts.urls')),
    path('api/v1/status/', include('status.urls')),
    path('api/v1/rest-auth/login/', CustomLoginView.as_view(), name='rest_login'),
    path('api/v1/rest-auth/logout/', CustomLogoutView.as_view(), name='rest_logout'),
    # Filter out login/logout URLs from dj_rest_auth
    *[url for url in dj_rest_auth_urls.urlpatterns 
      if url.name not in ['rest_login', 'rest_logout']],
    path('api/v1/rest-auth/registration/', CustomRegisterView.as_view(), name='rest_register'),
]
