from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer

class IsEmployerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (request.user.is_authenticated and 
                hasattr(request.user, 'profile') and 
                request.user.profile.is_employer)

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_active=True).annotate(
        application_count=Count('applications')
    )
    serializer_class = JobSerializer
    permission_classes = [IsEmployerOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        total_jobs = Job.objects.filter(is_active=True).count()
        total_applications = Application.objects.count()
        
        top_jobs = Job.objects.annotate(
            app_count=Count('applications')
        ).order_by('-app_count')[:5]
        
        job_types = Job.objects.values('job_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'top_jobs': JobSerializer(top_jobs, many=True).data,
            'job_types': list(job_types),
        })

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.is_employer:
            return Application.objects.filter(job__posted_by=user)
        return Application.objects.filter(applicant=user)
    
    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)