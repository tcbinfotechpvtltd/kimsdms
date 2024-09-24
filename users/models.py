from django.db import models
from django.contrib.auth.models import AbstractUser
from organization.models import Organization, Roles


class User(AbstractUser):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_users', null=True, blank=True)
    roles = models.ManyToManyField(Roles, related_name='role_users')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)



class CreatorUpdator(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_by_user')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='updated_by_user')

    class Meta:
        abstract = True



