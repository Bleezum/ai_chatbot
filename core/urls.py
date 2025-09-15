# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('info/', views.info, name='info'),
    path('courses/', views.student_courses, name='student_courses'),
    path('courses/register/', views.course_registration, name='course_registration'),
    path('courses/register/<int:offering_id>/', views.register_course, name='register_course'),
    path('courses/drop/<int:enrollment_id>/', views.drop_course, name='drop_course'),
    path("timetable/", views.student_timetable, name="student_timetable"),
    path('grades/', views.student_grades_view, name='grades'),
    path('finance/', views.student_finance_view, name='finance'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/download/<int:pk>/', views.download_assignment, name='download_assignment'),
    path('library/resources/', views.library_resources, name='library_resources'),
    path("assignment-chat/", views.assignment_chat, name="assignment_chat"),
    path("assignment-chat/ask/", views.assignment_chat_ask, name="assignment_chat_ask"),
    path('academic-chat/', views.academic_chat, name='academic_chat'),
    path('academic-chat/ask/', views.academic_chat_ask, name='academic_chat_ask'),
    path('my-timetable/', views.my_timetable, name='my_timetable'),
    path('generate-timetable/', views.generate_timetable, name='generate_timetable'),
    path('generate-questions/', views.generate_question_view, name='generate_questions'),
    path("program-enrollment/", views.program_enrollment_view, name="program_enrollment"),
]