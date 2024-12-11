from django.urls import path
from . import views
from .views import StatusDetail, StatusList
from django.conf import settings
from django.conf.urls.static import static
from .views import StatusSerializer

app_name = 'status'
urlpatterns = [
    path("", StatusList.as_view(), name="status_list"),
    path("<int:status_id>", StatusDetail.as_view(), name="status_detail"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)#for saving the pics
