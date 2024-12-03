from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView

from notification_app.serializers import NotificationDataDetailSerializer, NotificationDataListSerializer, NotificationDataSerializer
from .models import Notification, NotificationRecipient, User
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics

from django.db.models import Exists, Subquery, OuterRef, BooleanField
from django.utils import timezone


class NotificationListAPI(ListAPIView):
    serializer_class = NotificationDataListSerializer
    queryset = Notification.objects.all()


    def get_queryset(self):
        user = self.request.user  
        qs = self.queryset.filter(recipients=user).annotate(
            is_seen=Subquery(
                NotificationRecipient.objects.filter(
                    user=user, notification_id=OuterRef('id')
                ).values('is_seen')[:1],  
                output_field=BooleanField()
            )
        )
            
        return qs
    

class NotificationRetireveAPI(RetrieveAPIView):
    serializer_class = NotificationDataDetailSerializer
    queryset = Notification.objects.all()

    def get_object(self):
        user = self.request.user
        obj =  super().get_object()
        NotificationRecipient.objects.filter(notification=obj, user=user).update(
            is_seen=True, seen_at = timezone.now()
        )
        return obj


    def get_queryset(self):
        user = self.request.user  
        qs = self.queryset.filter(recipients=user).annotate(
            is_seen=Subquery(
                NotificationRecipient.objects.filter(
                    user=user, notification_id=OuterRef('id')
                ).values('is_seen')[:1],  
                output_field=BooleanField()
            ),
            seen_at=Subquery(
                NotificationRecipient.objects.filter(
                    user=user, notification_id=OuterRef('id')
                ).values('seen_at')[:1],  
                output_field=BooleanField()
            )
        
        )
        return qs
    
