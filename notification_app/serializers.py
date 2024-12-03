from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from notification_app.models import Notification

class NotificationDataSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'description', 'created_at', 'module']


class NotificationDataListSerializer(ModelSerializer):
    is_seen = serializers.BooleanField()
    class Meta:
        model = Notification
        fields = ['id', 'title', 'is_seen', 'created_at', 'module']

class NotificationDataDetailSerializer(NotificationDataSerializer):
    is_seen = serializers.BooleanField()
    seen_at = serializers.DateTimeField()
    class Meta(NotificationDataSerializer.Meta):
        fields = NotificationDataSerializer.Meta.fields + ['is_seen', 'seen_at']
