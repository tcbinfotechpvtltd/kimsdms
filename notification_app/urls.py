from django.urls import path

from .views import  NotificationListAPI, NotificationRetireveAPI

urlpatterns = [
    path('list/', NotificationListAPI.as_view(), name='notification-list'),
    path('retrieve/<int:pk>', NotificationRetireveAPI.as_view(), name='NotificationRetireveAPI'),

]