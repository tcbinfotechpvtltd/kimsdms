from django.db import models


class TimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

class CreatorUpdator(models.Model):
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        related_name='%(class)s_created_by_user'
    )
    updated_by = models.ForeignKey(
        'users.User', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='%(class)s_updated_by_user'
    )

    class Meta:
        abstract = True

