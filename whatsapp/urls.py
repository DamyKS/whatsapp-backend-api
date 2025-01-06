
from django.contrib import admin
from django.urls import path , include 
from dj_rest_auth import urls as dj_rest_auth_urls
from accounts.views import CustomRegisterView, CustomLoginView, CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('', include('accounts.urls')),
    path('status/', include('status.urls')),
    # path('rest-auth/login/', CustomLoginView.as_view(), name='rest_login'),
    # path('rest-auth/logout/', CustomLogoutView.as_view(), name='rest_login'),
    # path('rest-auth/', include('dj_rest_auth.urls')),
    path('rest-auth/login/', CustomLoginView.as_view(), name='rest_login'),
    path('rest-auth/logout/', CustomLogoutView.as_view(), name='rest_logout'),
    # Filter out login/logout URLs from dj_rest_auth
    *[url for url in dj_rest_auth_urls.urlpatterns 
      if url.name not in ['rest_login', 'rest_logout']],
    path('rest-auth/registration/', CustomRegisterView.as_view(), name='rest_register'),
]
