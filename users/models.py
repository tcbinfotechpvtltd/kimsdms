from django.db import models
from django.contrib.auth.models import AbstractUser

from Dms.common.models import CreatorUpdator, TimeStamp
from organization.models import Record, RecordDocument, Roles


class User(AbstractUser):
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, related_name='org_users', null=True, blank=True)
    roles = models.ManyToManyField('organization.Roles', related_name='role_users')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)



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

