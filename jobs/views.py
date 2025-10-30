from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views.generic import DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from .models import Job, Application, UserProfile
from .forms import UserRegistrationForm, JobForm, ApplicationForm, ProfileForm
from django.views.decorators.http import require_POST

# Home View
def home(request):
    recent_jobs = Job.objects.filter(is_active=True)[:6]
    context = {
        'recent_jobs': recent_jobs,
        'total_jobs': Job.objects.filter(is_active=True).count(),
        'total_companies': Job.objects.values('company_name').distinct().count(),
    }
    return render(request, 'jobs/home.html', context)

# Registration View
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data.get('user_type')
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                is_employer=(user_type == 'employer'),
                is_candidate=(user_type == 'candidate')
            )
            
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('job_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'jobs/register.html', {'form': form})

# Custom Login View
class CustomLoginView(LoginView):
    template_name = 'jobs/login.html'
    redirect_authenticated_user = True

# Job List View (Function-Based)
def job_list(request):
    jobs = Job.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Filter by job type
    job_type = request.GET.get('job_type', '')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    # Pagination
    paginator = Paginator(jobs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'job_type': job_type,
    }
    return render(request, 'jobs/job_list.html', context)

# Job Detail View (Class-Based)
class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_applied'] = Application.objects.filter(
                job=self.object,
                applicant=self.request.user
            ).exists()
        return context

# Create Job View (Function-Based)
@login_required
def job_create(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_employer:
        messages.error(request, 'Only employers can post jobs.')
        return redirect('job_list')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form})

# Update Job View (Class-Based)
class JobUpdateView(LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        job = self.get_object()
        if job.posted_by != request.user:
            messages.error(request, 'You can only edit your own job postings.')
            return redirect('job_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        messages.success(self.request, 'Job updated successfully!')
        return reverse_lazy('job_detail', kwargs={'pk': self.object.pk})

# Delete Job View (Class-Based)
class JobDeleteView(LoginRequiredMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('my_jobs')
    
    def dispatch(self, request, *args, **kwargs):
        job = self.get_object()
        if job.posted_by != request.user:
            messages.error(request, 'You can only delete your own job postings.')
            return redirect('job_list')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Job deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Apply for Job
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    if not hasattr(request.user, 'profile') or not request.user.profile.is_candidate:
        messages.error(request, 'Only candidates can apply for jobs.')
        return redirect('job_detail', pk=job_id)
    
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', pk=job_id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            
            # Send email notification
            try:
                send_mail(
                    subject=f'New Application for {job.title}',
                    message=f'{request.user.username} has applied for {job.title}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[job.posted_by.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('application_success', pk=application.pk)
    else:
        form = ApplicationForm()
    
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

# Application Success
@login_required
def application_success(request, pk):
    application = get_object_or_404(Application, pk=pk, applicant=request.user)
    return render(request, 'jobs/application_success.html', {'application': application})

# My Jobs (for employers)
@login_required
def my_jobs(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_employer:
        messages.error(request, 'This page is only for employers.')
        return redirect('job_list')
    
    jobs = Job.objects.filter(posted_by=request.user).annotate(
        app_count=Count('applications')
    )
    return render(request, 'jobs/my_jobs.html', {'jobs': jobs})

# My Applications (for candidates)
@login_required
def my_applications(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_candidate:
        messages.error(request, 'This page is only for candidates.')
        return redirect('job_list')
    
    applications = Application.objects.filter(applicant=request.user)
    return render(request, 'jobs/my_applications.html', {'applications': applications})

# View Applications for a Job
@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    applications = job.applications.all()
    return render(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications
    })

# Update application status (Employer only)
@login_required
@require_POST
def update_application_status(request, job_id, application_id, action):
    job = get_object_or_404(Job, id=job_id, posted_by=request.user)
    application = get_object_or_404(Application, id=application_id, job=job)
    action_map = {
        'accept': 'A',
        'review': 'R',
        'decline': 'D',
    }
    status_code = action_map.get(action)
    if not status_code:
        messages.error(request, 'Invalid action.')
        return redirect('job_applications', job_id=job.id)

    application.status = status_code
    application.save(update_fields=['status'])
    messages.success(request, f"Application marked as {'Accepted' if status_code=='A' else 'Reviewed' if status_code=='R' else 'Declined'}.")
    return redirect('job_applications', job_id=job.id)

# Profile View
@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email')
            request.user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
    
    return render(request, 'jobs/profile.html', {'form': form})

# Analytics Dashboard
@login_required
def dashboard(request):
    if hasattr(request.user, 'profile') and request.user.profile.is_employer:
        # Employer dashboard
        my_jobs = Job.objects.filter(posted_by=request.user)
        total_jobs = my_jobs.count()
        active_jobs = my_jobs.filter(is_active=True).count()
        total_applications = Application.objects.filter(job__posted_by=request.user).count()
        
        # Most applied jobs
        top_jobs = my_jobs.annotate(
            app_count=Count('applications')
        ).order_by('-app_count')[:5]
        
        context = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'top_jobs': top_jobs,
            'is_employer': True,
        }
    else:
        # Candidate dashboard
        my_applications = Application.objects.filter(applicant=request.user)
        context = {
            'total_applications': my_applications.count(),
            'pending': my_applications.filter(status='P').count(),
            'reviewed': my_applications.filter(status='R').count(),
            'accepted': my_applications.filter(status='A').count(),
            'recent_applications': my_applications[:5],
            'is_employer': False,
        }
    
    return render(request, 'jobs/dashboard.html', context)