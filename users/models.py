from django.db import models
from django.contrib.auth.models import AbstractUser

from Dms.common.models import CreatorUpdator, TimeStamp
from organization.models import Record, RecordDocument, Roles
import os


def get_photo_upload_path(instance, file_name):
    photo_extension = os.path.splitext(file_name)[1]
    return f'users/{instance.id}/profile_pic{photo_extension}'

def get_signature_upload_path(instance, file_name):
    sign_extension = os.path.splitext(file_name)[1]
    return f'user/{instance.id}/signature{sign_extension}'

class User(AbstractUser):
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, related_name='org_users', null=True, blank=True)
    roles = models.ManyToManyField('organization.Roles', related_name='role_users')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    photo = models.ImageField(upload_to=get_photo_upload_path, null=True, blank=True)
    signature = models.ImageField(upload_to=get_signature_upload_path, null=True, blank=True)
    designation= models.CharField(max_length=200, null=True, blank=True)
    contact = models.CharField(max_length=15, null=True, blank=True)  # New field for contact number
    is_online = models.BooleanField(default=False)
    channel_name = models.CharField(max_length=200, null=True, blank=True)


class RecordLog(CreatorUpdator, TimeStamp):
    ACTIONS = (
        ('approved', 'approved'),
        ('rejected', 'rejected'),
        ('edited', 'edited'),
        ('commented', 'commented'),
        ('attached', 'attached')
    )
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='logs')
    doc = models.ForeignKey(RecordDocument, on_delete=models.CASCADE, related_name='logs_doc', null=True, blank=True)
    action = models.CharField(choices=ACTIONS)
    comment = models.TextField(null=True, blank=True)
    followup_users = models.ManyToManyField(User, null=True, blank=True, related_name='followup_user_logs')
    followup_user_hod = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='followup_user_hod_logs')
    

