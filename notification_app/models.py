import json
import time
from django.db import models

from users.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Notification(models.Model):
    module = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    recipients = models.ManyToManyField(User, through="NotificationRecipient", related_name="notifications_set")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


    @classmethod
    def create_notification_object(cls, title, description, recipients, module):
        instance = cls.objects.create(module=module, title=title, description=description)
        instance.recipients.set(recipients)
        return instance

    @classmethod
    def send_notifications_on_socket(cls, notification_obj, recipient_users):
        from notification_app.serializers import NotificationDataSerializer

        channel_layer = get_channel_layer()

        print(channel_layer)

        notification_data = json.dumps(
            {
            "code": 200,
            "data":NotificationDataSerializer(notification_obj).data
            }
        )

        if len(recipient_users) <= 10:
            for user in recipient_users:
                if user.channel_name:
                    print(f"Sending message to user: {user.username} with channel: {user.channel_name}")
                    # Send the message directly to each user's channel
                    async_to_sync(channel_layer.send)(
                        user.channel_name,  # Send to the user's specific channel
                        {
                            "type": "chat.message",  # Define the type of message
                            "text": notification_data,  # The message content (notification data)
                        }
                    )


        else:
            group_name = str(time.time()).replace(".", "") + f"_{notification_obj.id}"

            for user in recipient_users:
                if user.channel_name:
                    print(user.channel_name)
                    res = async_to_sync(channel_layer.group_add)(group_name, user.channel_name)
                    print(res)

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "chat.message",
                    "text": notification_data,
                }
            )

            for user in recipient_users:
                if user.channel_name:
                    async_to_sync(channel_layer.group_discard)(group_name, user.channel_name)


    @classmethod
    def send_notification(cls, title, description, recipients, module):
        notification_obj = Notification.create_notification_object(title, description, recipients, module)
        try:
            Notification.send_notifications_on_socket(notification_obj, notification_obj.recipients.all())
        except:
            pass



class NotificationRecipient(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='notification_recipients')
    is_seen = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
            return f"{self.notification}/{self.user}/{self.is_seen}"


class RecordFollowupUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="record_followups")
    record = models.ForeignKey("organization.Record", on_delete=models.CASCADE, related_name="record_followups")
    record_log = models.ForeignKey("users.RecordLog", on_delete=models.CASCADE, related_name="record_followups")
    hod_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="hod_record_followups")
