from django.contrib import admin

from .models import  RecordDocument, Record, Organization, Roles, DepartMent, RecordRoleStatus, Workflow, WorkFlowLog, FlowPipeLine, MasterDepartment, PlantMasterSuperitandent

admin.site.register(RecordDocument)
admin.site.register(Record)
admin.site.register(Organization)
admin.site.register(Roles)
admin.site.register(RecordRoleStatus)

@admin.register(PlantMasterSuperitandent)
class PlantMasterSuperitandentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'plnt', 'is_active']
    list_filter = ['is_active', 'plnt']
    search_fields = ['name']

@admin.register(DepartMent)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sloc', 'plnt', 'is_active']
    list_filter = ['is_active', 'plnt']
    search_fields = ['name', 'sloc']


@admin.register(Workflow)
class WorkFlowAdmin(admin.ModelAdmin):
    list_display = ['id', 'work_flow_name', 'work_flow_sloc']
    search_fields = ['work_flow_name', 'work_flow_sloc']


@admin.register(FlowPipeLine)
class FlowPipelineAdmin(admin.ModelAdmin):
    list_display = ['id', 'workflow', 'role', 'wf_prev_level', 'is_active']
    list_filter = ['role', 'workflow', 'is_active']




@admin.register(WorkFlowLog)
class WorkFlowLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'flow_pipe_line', 'record', 'status', 'user']
    list_filter = ['user', 'record', 'status']

@admin.register(MasterDepartment)
class MasterDepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
