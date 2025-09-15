from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone

from accounts.forms import UserRegistrationForm
from core.models import Enrollment, Semester, Assignment


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_template_names(self):
        user = self.request.user
        if user.role == 'student':
            return ['dashboard/student_dashboard.html']
        elif user.role == 'lecturer':
            return ['dashboard/lecturer_dashboard.html']
        elif user.role == 'admin':
            return ['dashboard/admin_dashboard.html']
        return ['dashboard/dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.role == 'student':
            current_semester = Semester.objects.filter(is_current=True).first()
            if current_semester:
                current_courses = Enrollment.objects.filter(
                    student=user,
                    course_offering__semester=current_semester,
                    is_active=True
                )
                context['current_courses_count'] = current_courses.count()
            else:
                context['current_courses_count'] = 0

            
            pending_assignments = Assignment.objects.filter(
                due_date__gte=timezone.now().date()
            ).count()
            context['pending_assignments'] = pending_assignments

        return context
