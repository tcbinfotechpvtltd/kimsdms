from django.contrib import admin

from .models import Notification, NotificationRecipient, RecordFollowupUser


admin.site.register(Notification)
admin.site.register(NotificationRecipient)
admin.site.register(RecordFollowupUser)
