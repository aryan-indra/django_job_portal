# jobs/tests.py - Unit Tests

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Job, Application, UserProfile
from .forms import JobForm, ApplicationForm, UserRegistrationForm
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            is_employer=True
        )
        
    def test_job_creation(self):
        """Test job model creation"""
        job = Job.objects.create(
            title='Python Developer',
            description='Looking for Python developer',
            company_name='Tech Corp',
            location='Mumbai',
            job_type='FT',
            posted_by=self.user
        )
        self.assertEqual(job.title, 'Python Developer')
        self.assertEqual(str(job), 'Python Developer at Tech Corp')
        self.assertTrue(job.is_active)
        
    def test_application_creation(self):
        """Test application model creation"""
        job = Job.objects.create(
            title='Django Developer',
            description='Django expert needed',
            company_name='WebCo',
            location='Delhi',
            posted_by=self.user
        )
        
        candidate = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=candidate, is_candidate=True)
        
        resume_file = SimpleUploadedFile(
            "resume.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        application = Application.objects.create(
            job=job,
            applicant=candidate,
            resume=resume_file,
            message='I am interested'
        )
        
        self.assertEqual(application.job, job)
        self.assertEqual(application.applicant, candidate)
        self.assertEqual(application.status, 'P')


class FormTests(TestCase):
    def test_job_form_valid(self):
        """Test valid job form"""
        form_data = {
            'title': 'Software Engineer',
            'description': 'We are looking for a software engineer',
            'company_name': 'TechStart',
            'location': 'Bangalore',
            'job_type': 'FT',
            'salary_range': '10-15 LPA'
        }
        form = JobForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_job_form_invalid_title(self):
        """Test job form with short title"""
        form_data = {
            'title': 'Dev',  # Too short
            'description': 'Description',
            'company_name': 'Company',
            'location': 'Location',
            'job_type': 'FT'
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        
    def test_registration_form_valid(self):
        """Test valid registration form"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_pass123',
            'password2': 'complex_pass123',
            'user_type': 'candidate'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='pass123'
        )
        self.employer_profile = UserProfile.objects.create(
            user=self.employer,
            is_employer=True
        )
        
        self.candidate = User.objects.create_user(
            username='candidate',
            email='candidate@example.com',
            password='pass123'
        )
        self.candidate_profile = UserProfile.objects.create(
            user=self.candidate,
            is_candidate=True
        )
        
    def test_home_view(self):
        """Test home page loads correctly"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/home.html')
        
    def test_job_list_view(self):
        """Test job list view"""
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jobs/job_list.html')
        
    def test_job_create_requires_login(self):
        """Test job creation requires authentication"""
        response = self.client.get(reverse('job_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_job_create_employer_only(self):
        """Test only employers can create jobs"""
        self.client.login(username='candidate', password='pass123')
        response = self.client.get(reverse('job_create'))
        self.assertEqual(response.status_code, 302)  # Redirected
        
    def test_job_create_by_employer(self):
        """Test employer can access job creation"""
        self.client.login(username='employer', password='pass123')
        response = self.client.get(reverse('job_create'))
        self.assertEqual(response.status_code, 200)
        
    def test_job_detail_view(self):
        """Test job detail view"""
        job = Job.objects.create(
            title='Test Job',
            description='Description',
            company_name='Company',
            location='Location',
            posted_by=self.employer
        )
        response = self.client.get(reverse('job_detail', kwargs={'pk': job.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Job')


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        UserProfile.objects.create(user=self.user, is_candidate=True)
        
    def test_login_view(self):
        """Test login page loads"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
    def test_successful_login(self):
        """Test user can login successfully"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'pass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
    def test_registration_view(self):
        """Test registration page loads"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)


class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            is_employer=True
        )
        
        self.job = Job.objects.create(
            title='API Test Job',
            description='Testing API',
            company_name='TestCo',
            location='Test City',
            posted_by=self.user
        )
        
    def test_job_list_api(self):
        """Test job list API endpoint"""
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        
    def test_job_detail_api(self):
        """Test job detail API endpoint"""
        response = self.client.get(f'/api/jobs/{self.job.pk}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'API Test Job')
        
    def test_analytics_api(self):
        """Test analytics API endpoint"""
        response = self.client.get('/api/jobs/analytics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_jobs', data)
        self.assertIn('total_applications', data)


# Run tests with:
# python manage.py test
# or with pytest:
# pytest