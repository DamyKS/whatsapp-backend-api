from django.urls import path, include
from .views import ProfileDetail
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'accounts'
urlpatterns = [
    path("profile/", ProfileDetail.as_view(), name="profile_detail"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)#for saving the pics
