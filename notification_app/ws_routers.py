from .consumers import NotificationsConsumer
from django.urls import path



websocket_url_patterns = [
    path('notifications/<str:token>', NotificationsConsumer.as_asgi())
]
