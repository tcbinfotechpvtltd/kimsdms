from rest_framework.serializers import ModelSerializer

from notification_app.models import Notification

class NotificationDataSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'description', 'created_at', 'module']