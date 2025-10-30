from rest_framework import serializers
from .models import Job, Application
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class JobSerializer(serializers.ModelSerializer):
    posted_by = UserSerializer(read_only=True)
    application_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'company_name', 'location', 
                  'job_type', 'salary_range', 'posted_by', 'created_at', 
                  'is_active', 'application_count']
        read_only_fields = ['created_at']

class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    applicant = UserSerializer(read_only=True)
    
    class Meta:
        model = Application
        fields = ['id', 'job', 'applicant', 'resume', 'message', 
                  'status', 'submitted_at']
        read_only_fields = ['submitted_at', 'status']