from django.db import models
from django.contrib.auth.models import AbstractUser

from Dms.common.models import CreatorUpdator, TimeStamp
from organization.models import Record, RecordDocument, Roles


def get_photo_upload_path(instance, file_name):
    return f'user_profile_pics/{instance.id}/{file_name}'

def get_signature_upload_path(instance, file_name):
    return f'user_signatures/{instance.id}/{file_name}'


class User(AbstractUser):
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, related_name='org_users', null=True, blank=True)
    roles = models.ManyToManyField('organization.Roles', related_name='role_users')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    photo = models.ImageField(upload_to=get_photo_upload_path, null=True, blank=True)
    signature = models.ImageField(upload_to=get_signature_upload_path, null=True, blank=True)
    contact = models.CharField(max_length=15, null=True, blank=True)  # New field for contact number


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
    # user = models.ForeignKey(User, on_delete=models.CASCADE)

