from django.contrib import admin
from .models import User, RecordLog

# Register your models here.
admin.site.register(User)
admin.site.register(RecordLog)
