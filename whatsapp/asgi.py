import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp.settings')
import django 
from django.core.asgi import get_asgi_application

application = get_asgi_application()
