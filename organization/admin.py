from django.contrib import admin

from .models import  RecordDocument, Record, Organization, Roles, DepartMent, RecordRoleStatus

admin.site.register(RecordDocument)
admin.site.register(Record)
admin.site.register(Organization)
admin.site.register(Roles)
admin.site.register(RecordRoleStatus)

@admin.register(DepartMent)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sloc', 'plnt', 'is_active']
    list_filter = ['is_active', 'plnt']
    search_fields = ['name', 'sloc']