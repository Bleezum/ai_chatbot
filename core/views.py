# core/views.py

# =========================
# Standard Library Imports
# =========================
import json
from datetime import timedelta

# =========================
# Django Imports
# =========================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe

# =========================
# Third-Party Libraries
# =========================
import markdown

# =========================
# Local Imports
# =========================
from core.ai_quetions_gen import generate_questions
from core.ai_care import AcademicAIService
from core.ai_timetable_creater import TimetableAIService
from core.ai_assignment import AIAssignmentService
from core.ai_service import AIService
from .models import (
    Event, Program, Assignment, Course,
    CourseOffering, Enrollment, FinanceRecord,
    Semester, ProgramEnrollment
)

# =========================
# Home & Dashboard
# =========================
def home(request):
    return render(request, 'core/home.html')


# =========================
# Course Management
# =========================
@login_required
def student_courses(request):
    """Display student's enrolled courses"""
    current_semester = Semester.objects.filter(is_current=True).first()
    enrollments = Enrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course_offering', 'course_offering__course', 'course_offering__semester')

    context = {
        'current_enrollments': enrollments.filter(course_offering__semester=current_semester),
        'past_enrollments': enrollments.exclude(course_offering__semester=current_semester),
        'current_semester': current_semester,
    }
    return render(request, 'dashboard/courses.html', context)


@login_required
def course_registration(request):
    """Display available courses for registration"""
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.warning(request, "No active semester found for registration.")
        return redirect('student_courses')

    today = timezone.now().date()
    if today < current_semester.registration_start:
        messages.info(request, f"Registration opens on {current_semester.registration_start}")
        return redirect('student_courses')
    elif today > current_semester.registration_end:
        messages.warning(request, "Registration period has ended")
        return redirect('student_courses')

    program_enrollment = ProgramEnrollment.objects.filter(
        student=request.user, is_active=True
    ).first()
    if not program_enrollment:
        messages.error(request, "You are not enrolled in any program.")
        return redirect('student_courses')

    available_offerings = CourseOffering.objects.filter(
        semester=current_semester, is_active=True
    ).select_related('course', 'lecturer').prefetch_related('enrollments')

    enrolled_courses = Enrollment.objects.filter(
        student=request.user, course_offering__semester=current_semester, is_active=True
    ).values_list('course_offering_id', flat=True)

    context = {
        'current_semester': current_semester,
        'program_enrollment': program_enrollment,
        'available_offerings': available_offerings,
        'enrolled_courses': enrolled_courses,
    }
    return render(request, 'dashboard/course_registration.html', context)


@login_required
def register_course(request, offering_id):
    """Register for a course"""
    offering = get_object_or_404(CourseOffering, id=offering_id, is_active=True)
    current_semester = offering.semester
    today = timezone.now().date()

    if today < current_semester.registration_start:
        messages.error(request, "Registration period has not started yet.")
        return redirect('course_registration')
    elif today > current_semester.add_drop_deadline:
        messages.error(request, "Add/drop period has ended.")
        return redirect('course_registration')

    if offering.is_full():
        messages.error(request, f"{offering.course.code} is full.")
        return redirect('course_registration')

    if Enrollment.objects.filter(student=request.user, course_offering=offering, is_active=True).exists():
        messages.warning(request, f"You are already enrolled in {offering.course.code}.")
        return redirect('course_registration')

    # Check prerequisites
    for prereq in offering.course.required_prerequisites.all():
        completed = Enrollment.objects.filter(
            student=request.user,
            course_offering__course=prereq.prerequisite,
            status='completed',
            is_active=True
        )
        if prereq.minimum_grade:
            completed = completed.filter(grade__lte=prereq.minimum_grade)

        if not completed.exists() and prereq.is_mandatory:
            messages.error(request, f"Missing prerequisite: {prereq.prerequisite.code}")
            return redirect('course_registration')

    Enrollment.objects.create(student=request.user, course_offering=offering, status='registered')
    messages.success(request, f"Successfully enrolled in {offering.course.code}")
    return redirect('student_courses')


@login_required
def drop_course(request, enrollment_id):
    """Drop a course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    current_semester = enrollment.course_offering.semester
    today = timezone.now().date()

    if today > current_semester.add_drop_deadline:
        messages.error(request, "Add/drop period has ended.")
        return redirect('student_courses')

    enrollment.is_active = False
    enrollment.status = 'withdrawn'
    enrollment.save()

    offering = enrollment.course_offering
    offering.enrolled -= 1
    offering.save()

    messages.success(request, f"Successfully dropped {offering.course.code}")
    return redirect('student_courses')


# =========================
# Timetable & Grades
# =========================
@login_required
def student_timetable(request):
    """Show timetable"""
    current_semester = Semester.objects.filter(is_current=True).first()
    enrollments = Enrollment.objects.filter(
        student=request.user,
        course_offering__semester=current_semester,
        is_active=True
    ).select_related("course_offering__course", "course_offering__lecturer")

    return render(request, "dashboard/timetable.html", {
        "current_semester": current_semester,
        "enrollments": enrollments
    })


def student_grades_view(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related(
        'course_offering__course', 'course_offering__semester', 'course_offering__lecturer'
    )
    return render(request, 'dashboard/grades.html', {'enrollments': enrollments})


def student_finance_view(request):
    finance_records = FinanceRecord.objects.filter(student=request.user)
    return render(request, 'dashboard/finance.html', {'finance_records': finance_records})


# =========================
# Events & Assignments
# =========================
def event_list(request):
    return render(request, 'event_list.html', {'events': Event.objects.all()})


def assignment_list(request):
    assignments = Assignment.objects.all().order_by('-uploaded_at')
    return render(request, 'dashboard/assignments.html', {'assignments': assignments})


def download_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    return FileResponse(
        assignment.file.open('rb'),
        as_attachment=True,
        filename=assignment.file.name.split('/')[-1]
    )


# =========================
# AI: Assignment Helper
# =========================
assignment_ai = AIAssignmentService()

def assignment_chat(request):
    return render(request, "dashboard/assignment_chat.html")

@csrf_exempt
def assignment_chat_ask(request):
    if request.method == "POST":
        message = json.loads(request.body).get("message", "")
        if not message:
            return JsonResponse({"responses": []})

        guidance_json = assignment_ai.provide_guidance(message)
        try:
            guidance_list = json.loads(guidance_json)
        except Exception:
            guidance_list = [{"title": "Error", "description": "AI failed to respond.", "url": ""}]
        return JsonResponse({"responses": guidance_list})

    return JsonResponse({"responses": []})


# =========================
# AI: Question Generator
# =========================
@login_required
def generate_question_view(request):
    current_courses = Enrollment.objects.filter(student=request.user, is_active=True)\
        .select_related('course_offering__course')
    courses_list = [e.course_offering.course for e in current_courses]

    questions = []
    if request.method == "POST":
        course_id = int(request.POST.get("course"))
        topic = request.POST.get("topic")
        num_questions = int(request.POST.get("num_questions", 5))
        selected_course = next((c for c in courses_list if c.id == course_id), None)

        if selected_course:
            raw_questions = generate_questions(selected_course.name, topic, num_questions)
            questions = [mark_safe(markdown.markdown(q)) for q in raw_questions]

    return render(request, "dashboard/generate_question.html", {
        "courses": courses_list, "questions": questions
    })


# =========================
# AI: Library Resources
# =========================
def library_resources(request):
    enrolled_courses = Course.objects.filter(
        offerings__enrollments__student=request.user,
        offerings__enrollments__is_active=True
    ).distinct()

    resources, selected_course = [], None
    course_id = request.GET.get('course_id')

    if course_id:
        selected_course = get_object_or_404(Course, pk=course_id)
        ai = AIService()
        resources = ai.fetch_online_resources(course_name=selected_course.name, student=request.user)

    return render(request, 'dashboard/library.html', {
        'resources': resources, 'selected_course': selected_course,
        'enrolled_courses': enrolled_courses
    })


# =========================
# AI: Academic Assistant
# =========================
academic_ai = AcademicAIService()

@csrf_exempt
def academic_chat(request):
    return render(request, "academic_ai.html")

@csrf_exempt
def academic_chat_ask(request):
    if request.method == "POST":
        question = json.loads(request.body).get("message", "").strip()
        ai_response_text = academic_ai.provide_guidance(question)
        try:
            responses = json.loads(ai_response_text)
        except Exception:
            responses = [{
                "title": "CUEA Guidance",
                "description": ai_response_text,
                "url": "https://www.cuea.edu"
            }]
        return JsonResponse({"responses": responses})


# =========================
# AI: Timetable Generator
# =========================
timetable_ai = TimetableAIService()

@csrf_exempt
def my_timetable(request):
    return render(request, "dashboard/mytimetable.html", {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]})

@csrf_exempt
def generate_timetable(request):
    if request.method == "POST":
        courses = [{
            "code": e.course_offering.course.code,
            "name": e.course_offering.course.name,
            "credits": e.course_offering.course.credits
        } for e in Enrollment.objects.filter(student=request.user, is_active=True)]

        try:
            timetable = json.loads(timetable_ai.create_timetable(courses))
        except Exception:
            timetable = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}

        return JsonResponse({"timetable": timetable})


# =========================
# Program Enrollment
# =========================
@login_required
def program_enrollment_view(request):
    if request.method == "POST":
        program = get_object_or_404(Program, id=request.POST.get("program_id"), is_active=True)
        if ProgramEnrollment.objects.filter(student=request.user, program=program, is_active=True).exists():
            messages.warning(request, f"You are already enrolled in {program.name}.")
            return redirect("program_enrollment")

        expected_graduation = timezone.now().date() + timedelta(days=program.duration * 6 * 30)
        ProgramEnrollment.objects.create(student=request.user, program=program, expected_graduation=expected_graduation)

        messages.success(request, f"Successfully enrolled in {program.name}")
        return redirect("student_courses")

    return render(request, "dashboard/program_enrollment.html", {
        "programs": Program.objects.filter(is_active=True),
        "my_enrollments": ProgramEnrollment.objects.filter(student=request.user)
    })
    
    
#=======================
# importance
#==============
def info(request):
    return render(request, 'dashboard/info.html')


#==========================
# Events