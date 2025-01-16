from django.urls import re_path
from . import consumers
websocket_urlpatterns = [ 
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatRoomConsumer.as_asgi()),
    re_path(r'ws/call/(?P<user_name>\w+)/$', consumers.CallSignalingConsumer.as_asgi()),
]