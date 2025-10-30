from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

router = DefaultRouter()
router.register(r'jobs', api_views.JobViewSet, basename='api-job')
router.register(r'applications', api_views.ApplicationViewSet, basename='api-application')

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    
    # Jobs
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/update/', views.JobUpdateView.as_view(), name='job_update'),
    path('jobs/<int:pk>/delete/', views.JobDeleteView.as_view(), name='job_delete'),
    
    # Applications
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('application/<int:pk>/success/', views.application_success, name='application_success'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('jobs/<int:job_id>/applications/', views.job_applications, name='job_applications'),
    
    # Profile & Dashboard
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # API
    path('api/', include(router.urls)),
]