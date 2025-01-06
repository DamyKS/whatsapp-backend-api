import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "whatsapp.settings")
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
#from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path

import chat.routing


# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
   'websocket': AuthMiddlewareStack(
       URLRouter(
            chat.routing.websocket_urlpatterns
        )
   )
    
})
