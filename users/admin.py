from django.contrib import admin
from .models import User, RecordLog

# Register your models here.
admin.site.register(User)

@admin.register(RecordLog)
class RecordLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'action', 'created_by', 'created_at']
