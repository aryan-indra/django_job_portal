from django.contrib import admin
from .models import Job, Application, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_employer', 'is_candidate', 'phone']
    list_filter = ['is_employer', 'is_candidate']
    search_fields = ['user__username', 'user__email']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company_name', 'location', 'job_type', 'posted_by', 'created_at', 'is_active']
    list_filter = ['job_type', 'is_active', 'created_at']
    search_fields = ['title', 'company_name', 'location']
    date_hierarchy = 'created_at'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['applicant__username', 'job__title']
    date_hierarchy = 'submitted_at'