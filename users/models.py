from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, related_name='org_users', null=True, blank=True)
    roles = models.ManyToManyField('organization.Roles', related_name='role_users')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)



