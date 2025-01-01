
from django.contrib import admin
from django.urls import path , include 
from accounts.views import CustomRegisterView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('', include('accounts.urls')),
    path('status/', include('status.urls')),
    path('rest-auth/', include('dj_rest_auth.urls')),
    #path('rest-auth/registration/',include('dj_rest_auth.registration.urls')),
    path('rest-auth/registration/', CustomRegisterView.as_view(), name='rest_register'),
]
