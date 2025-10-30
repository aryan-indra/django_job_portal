from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os

def resume_upload_path(instance, filename):
    return f'resumes/{instance.applicant.username}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_employer = models.BooleanField(default=False)
    is_candidate = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Job(models.Model):
    JOB_TYPES = [
        ('FT', 'Full Time'),
        ('PT', 'Part Time'),
        ('CT', 'Contract'),
        ('IN', 'Internship'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=2, choices=JOB_TYPES, default='FT')
    salary_range = models.CharField(max_length=100, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} at {self.company_name}"
    
    def application_count(self):
        return self.applications.count()

class Application(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('R', 'Reviewed'),
        ('A', 'Accepted'),
        ('D', 'Declined'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        help_text="Upload your resume (PDF, DOC, or DOCX format, max 5MB)"
    )
    message = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['job', 'applicant']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"