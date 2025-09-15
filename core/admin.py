# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Assignment, Faculty, Department, ProgramType, Program, Course, 
    CoursePrerequisite, ProgramCurriculum, Semester,
    CourseOffering, Enrollment, ProgramEnrollment,FinanceRecord
)

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dean', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code', 'name', 'dean__username', 'dean__first_name', 'dean__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Leadership', {
            'fields': ('dean',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'code', 'name', 'head_of_department', 'created_at')
    list_filter = ('faculty', 'created_at')
    search_fields = ('code', 'name', 'faculty__name', 'head_of_department__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('faculty', 'code', 'name', 'description')
        }),
        ('Leadership', {
            'fields': ('head_of_department',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProgramType)
class ProgramTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'duration_years')
    list_filter = ('level',)
    search_fields = ('name', 'description')
    fieldsets = (
        ('Program Type Information', {
            'fields': ('name', 'description', 'level', 'duration_years')
        }),
    )

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'department', 'program_type', 'category',
        'tuition_fee', 'registration_fee', 'exam_fee', 'other_fees',
        'is_active', 'total_credits'
    )
    list_filter = ('department', 'program_type', 'category', 'is_active')
    search_fields = ('code', 'name', 'department__name')
    readonly_fields = ('created_at', 'updated_at', 'current_students_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'program_type', 'code', 'name', 'description')
        }),
        ('Program Details', {
            'fields': ('category', 'duration', 'total_credits', 'is_active')
        }),
        ('Fees', {
            'fields': ('tuition_fee', 'registration_fee', 'exam_fee', 'other_fees')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Leadership', {
            'fields': ('program_coordinator',)
        }),
        ('Statistics', {
            'fields': ('current_students_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def current_students_count(self, obj):
        return obj.current_students_count()
    current_students_count.short_description = 'Current Students'

class CoursePrerequisiteInline(admin.TabularInline):
    model = CoursePrerequisite
    fk_name = 'course'
    extra = 1
    verbose_name = "Prerequisite"
    verbose_name_plural = "Prerequisites"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credits', 'level', 'course_type', 'is_active', 'enrolled_students_count')
    list_filter = ('department', 'level', 'course_type', 'is_active')
    search_fields = ('code', 'name', 'department__name')
    readonly_fields = ('created_at', 'updated_at', 'enrolled_students_count')
    inlines = [CoursePrerequisiteInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'code', 'name', 'description')
        }),
        ('Course Details', {
            'fields': ('credits', 'level', 'course_type', 'is_active')
        }),
        ('Learning Outcomes', {
            'fields': ('learning_outcomes',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('enrolled_students_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def enrolled_students_count(self, obj):
        return obj.enrolled_students_count()
    enrolled_students_count.short_description = 'Enrolled Students'

@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('course', 'prerequisite', 'is_mandatory', 'minimum_grade')
    list_filter = ('is_mandatory',)
    search_fields = ('course__code', 'course__name', 'prerequisite__code', 'prerequisite__name')

class ProgramCurriculumInline(admin.TabularInline):
    model = ProgramCurriculum
    extra = 1
    verbose_name = "Curriculum Item"
    verbose_name_plural = "Curriculum Items"

@admin.register(ProgramCurriculum)
class ProgramCurriculumAdmin(admin.ModelAdmin):
    list_display = ('program', 'course', 'semester', 'is_required', 'credits_contribution')
    list_filter = ('program', 'semester', 'is_required')
    search_fields = ('program__code', 'program__name', 'course__code', 'course__name')
    list_editable = ('semester', 'is_required', 'credits_contribution')

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_date', 'end_date', 'is_current', 'registration_status')
    list_filter = ('is_current',)
    search_fields = ('name', 'code')
    readonly_fields = ('registration_status',)
    fieldsets = (
        ('Semester Information', {
            'fields': ('name', 'code', 'is_current')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Registration Period', {
            'fields': ('registration_start', 'registration_end', 'add_drop_deadline')
        }),
    )

    def registration_status(self, obj):
        from django.utils import timezone
        now = timezone.now().date()
        
        if now < obj.registration_start:
            return format_html('<span style="color: orange;">Registration Not Started</span>')
        elif obj.registration_start <= now <= obj.registration_end:
            return format_html('<span style="color: green;">Registration Open</span>')
        else:
            return format_html('<span style="color: red;">Registration Closed</span>')
    registration_status.short_description = 'Registration Status'

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ('enrollment_date', 'grade', 'status')
    can_delete = False
    max_num = 0
    verbose_name = "Student Enrollment"
    verbose_name_plural = "Student Enrollments"

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'semester', 'section', 'lecturer', 'room', 'capacity', 'enrolled', 'available_seats_display', 'is_active')
    list_filter = ('semester', 'course__department', 'is_active')
    search_fields = ('course__code', 'course__name', 'lecturer__username', 'lecturer__first_name')
    readonly_fields = ('enrolled', 'available_seats', 'is_full')
    inlines = [EnrollmentInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'semester', 'section', 'is_active')
        }),
        ('Offering Details', {
            'fields': ('lecturer', 'room', 'schedule')
        }),
        ('Capacity', {
            'fields': ('capacity', 'enrolled', 'available_seats', 'is_full')
        }),
    )

    def available_seats_display(self, obj):
        seats = obj.available_seats()
        if seats > 10:
            color = 'green'
        elif seats > 0:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color}; font-weight: bold;">{seats}</span>')
    available_seats_display.short_description = 'Available Seats'

    def available_seats(self, obj):
        return obj.available_seats()
    available_seats.short_description = 'Available Seats'

    def is_full(self, obj):
        return obj.is_full()
    is_full.boolean = True
    is_full.short_description = 'Is Full?'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_offering', 'enrollment_date', 'grade', 'status', 'is_active')
    list_filter = ('course_offering__semester', 'grade', 'status', 'is_active')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 
                    'course_offering__course__code', 'course_offering__course__name')
    readonly_fields = ('enrollment_date',)
    list_editable = ('grade', 'status', 'is_active')
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course_offering', 'enrollment_date')
        }),
        ('Academic Details', {
            'fields': ('grade', 'status', 'credits_earned', 'is_active')
        }),
    )

class ProgramEnrollmentInline(admin.TabularInline):
    model = ProgramEnrollment
    extra = 0
    readonly_fields = ('enrollment_date', 'status', 'current_semester')
    can_delete = False
    max_num = 0
    verbose_name = "Program Enrollment"
    verbose_name_plural = "Program Enrollments"

@admin.register(ProgramEnrollment)
class ProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'enrollment_date', 'expected_graduation', 'status', 'current_semester', 'progress_display')
    list_filter = ('program', 'status', 'is_active')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 
                    'program__code', 'program__name')
    readonly_fields = ('enrollment_date', 'credits_completed', 'progress_percentage')
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'program', 'enrollment_date', 'expected_graduation')
        }),
        ('Academic Status', {
            'fields': ('status', 'current_semester', 'is_active')
        }),
        ('Progress', {
            'fields': ('credits_completed', 'progress_percentage'),
            'classes': ('collapse',)
        }),
    )

    def progress_display(self, obj):
        progress = obj.progress_percentage()
        if progress >= 80:
            color = 'green'
        elif progress >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<span style="color: {color}; font-weight: bold;">{progress:.1f}%</span>')
    progress_display.short_description = 'Progress'

    def credits_completed(self, obj):
        return obj.credits_completed()
    credits_completed.short_description = 'Credits Completed'

    def progress_percentage(self, obj):
        return obj.progress_percentage()
    progress_percentage.short_description = 'Progress (%)'
    
    
@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'program', 
        'transaction_type', 
        'description', 
        'amount', 
        'balance_after', 
        'transaction_date'
    )
    list_filter = (
        'transaction_type', 
        'transaction_date', 
        'program'
    )
    search_fields = (
        'student__username', 
        'student__first_name', 
        'student__last_name', 
        'description'
    )
    readonly_fields = ('balance_after', 'created_at', 'updated_at')
    ordering = ('-transaction_date',)
    date_hierarchy = 'transaction_date'

    fieldsets = (
        ('Student & Program', {
            'fields': ('student', 'program')
        }),
        ('Transaction Details', {
            'fields': ('transaction_type', 'description', 'amount')
        }),
        ('Balance Info', {
            'fields': ('balance_after',),
        }),
        ('Timestamps', {
            'fields': ('transaction_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lecturer', 'due_date', 'uploaded_at')
    list_filter = ('due_date', 'uploaded_at', 'lecturer')
    search_fields = ('title', 'description', 'lecturer__username')
    ordering = ('-uploaded_at',)

# Custom admin site header and title
admin.site.site_header = "University AI Assistant Portal Administration"
admin.site.site_title = "University Admin Portal"
admin.site.index_title = "Welcome to University Administration"