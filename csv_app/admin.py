from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CSVFile, TaskResult


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom user admin"""
    list_display = ('email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(CSVFile)
class CSVFileAdmin(admin.ModelAdmin):
    """CSV file admin"""
    list_display = ('original_name', 'user', 'file_size_mb', 
                   'upload_date', 'is_processed')
    list_filter = ('upload_date', 'is_processed')
    search_fields = ('original_name', 'user__email')
    readonly_fields = ('upload_date', 'file_size', 'file_size_mb')

    # Exclude file_size from form since it's auto-calculated
    exclude = ()

    def file_size_mb(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "Unknown"
    file_size_mb.short_description = 'File Size'

    def save_model(self, request, obj, form, change):
        """Override save to auto-calculate file_size"""
        if obj.file_path and hasattr(obj.file_path, 'size'):
            obj.file_size = obj.file_path.size
        else:
            obj.file_size = 0  # Default value if no file

        if not obj.original_name and obj.file_path:
            obj.original_name = obj.file_path.name

        super().save_model(request, obj, form, change)


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    """Task result admin"""
    list_display = ('task_id', 'user', 'operation', 'status', 
                   'created_at', 'completed_at')
    list_filter = ('operation', 'status', 'created_at')
    search_fields = ('task_id', 'user__email', 'csv_file__original_name')
    readonly_fields = ('task_id', 'created_at', 'started_at', 'completed_at')

    fieldsets = (
        ('Task Info', {'fields': ('task_id', 'user', 'csv_file', 'operation')}),
        ('Status', {'fields': ('status', 'error_message')}),
        ('Results', {'fields': ('result_file_path', 'processed_rows', 
                                'original_rows', 'operation_params')}),
        ('Timestamps', {'fields': ('created_at', 'started_at', 'completed_at')}),
    )
