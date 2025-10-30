from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Job, Application, UserProfile
from django.core.exceptions import ValidationError

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(
        choices=[('employer', 'Employer'), ('candidate', 'Candidate')],
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'company_name', 'location', 
                  'job_type', 'salary_range']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Senior Python Developer'}),
            'company_name': forms.TextInput(attrs={'placeholder': 'Your Company Name'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Mumbai, India'}),
            'salary_range': forms.TextInput(attrs={'placeholder': 'e.g., ₹8-12 LPA'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise ValidationError("Job title must be at least 5 characters long.")
        return title

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell the employer why you\'re a great fit for this role...'
            }),
        }
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if resume.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("Resume file size must be under 5MB.")
            ext = resume.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise ValidationError("Only PDF, DOC, and DOCX files are allowed.")
        return resume

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }