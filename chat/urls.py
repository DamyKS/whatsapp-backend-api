from django.urls import path, include
from .views import ChatList, ChatDetail, MessageDetail , CallSessionList
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'chat'
urlpatterns = [
    path("chats/", ChatList.as_view(), name="chats_list"),
    path("chats/<int:pk>/", ChatDetail.as_view(), name="chat_detail"),
    path("message/<int:pk>/", MessageDetail.as_view(), name="message"),
    path('<int:room_id>/', views.room, name= 'room'),

    path("calls/", CallSessionList.as_view(), name="calls_list"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)#for saving the pics
