"""
ASGI config for Dms project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dms.settings')

# application = get_asgi_application()


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from notification_app.consumers import NotificationsConsumer
from notification_app.middlewares import JwtAuthMiddleware
from notification_app.ws_routers import websocket_url_patterns
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pe_backend.settings')

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter([
            path("notifications/<str:token>", NotificationsConsumer.as_asgi()),
        ])
        # "websocket": JwtAuthMiddleware(URLRouter(websocket_url_patterns))

    }
)


