# core/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

class Faculty(models.Model):
    """Model representing university faculties"""
    code = models.CharField(max_length=10, unique=True, help_text="Faculty code (e.g., SCI, ENG, BUS)")
    name = models.CharField(max_length=100, help_text="Faculty name")
    description = models.TextField(blank=True, null=True)
    dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'lecturer'},
        related_name='dean_of_faculties'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Faculties"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

class Department(models.Model):
    """Model representing academic departments within faculties"""
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    code = models.CharField(max_length=10, help_text="Department code (e.g., CS, MATH, PHYS)")
    name = models.CharField(max_length=100, help_text="Department name")
    description = models.TextField(blank=True, null=True)
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'lecturer'},
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['faculty', 'code']
        unique_together = ['faculty', 'code']

    def __str__(self):
        return f"{self.faculty.code}/{self.code} - {self.name}"

class ProgramType(models.Model):
    """Model representing types of programs (Degree, Diploma, Certificate, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    duration_years = models.IntegerField(help_text="Typical duration in years")
    level = models.CharField(max_length=20, help_text="Academic level (e.g., Undergraduate, Graduate)")

    def __str__(self):
        return f"{self.name} - {self.level}"


class Program(models.Model):
    """Model representing academic programs (Degrees, Diplomas, Certificates, Postgraduate)"""

    PROGRAM_CATEGORIES = (
        ('degree', 'Degree Program'),
        ('diploma', 'Diploma Program'),
        ('certificate', 'Certificate Program'),
        ('postgrad', 'Postgraduate Program'),
    )

    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        related_name="programs"
    )
    program_type = models.ForeignKey(
        "ProgramType",
        on_delete=models.CASCADE,
        related_name="programs"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Program code (e.g., BSC-CS, DIP-BUS)"
    )
    name = models.CharField(max_length=200, help_text="Program name")
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in semesters")
    total_credits = models.IntegerField(help_text="Total credits required")
    category = models.CharField(
        max_length=20,
        choices=PROGRAM_CATEGORIES,
        default="degree"
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    program_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'lecturer'},
        related_name='coordinated_programs'
    )

    # 👇 Fee fields (all with defaults to avoid migration issues)
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Base tuition fee per semester"
    )
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="One-time registration fee"
    )
    exam_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Exam fee per semester"
    )
    other_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Any other applicable fees"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["department", "code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def current_students_count(self):
        """Return number of currently active students in this program"""
        return self.enrollments.filter(is_active=True).count()

    def total_fee_per_semester(self):
        """Calculate total fees for one semester"""
        return self.tuition_fee + self.exam_fee + self.other_fees

    def total_program_fee(self):
        """Calculate total fees for the entire program duration"""
        return (self.total_fee_per_semester() * self.duration) + self.registration_fee

class Course(models.Model):
    """Model representing individual courses"""
    COURSE_LEVELS = (
        ('100', 'Level 100 (Introductory)'),
        ('200', 'Level 200 (Intermediate)'),
        ('300', 'Level 300 (Advanced)'),
        ('400', 'Level 400 (Specialized)'),
        ('500', 'Level 500 (Graduate)'),
    )
    
    COURSE_TYPES = (
        ('core', 'Core Course'),
        ('elective', 'Elective Course'),
        ('lab', 'Laboratory'),
        ('project', 'Project Work'),
        ('thesis', 'Thesis/Dissertation'),
    )
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=20, help_text="Course code (e.g., CS101, MATH201)")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    level = models.CharField(max_length=3, choices=COURSE_LEVELS, default='100')
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='core')
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, 
                                         through='CoursePrerequisite',
                                         through_fields=('course', 'prerequisite'))
    is_active = models.BooleanField(default=True)
    learning_outcomes = models.TextField(blank=True, null=True, help_text="Course learning outcomes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'code']
        unique_together = ['department', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def enrolled_students_count(self):
     return Enrollment.objects.filter(course_offering__course=self, is_active=True).count()

class CoursePrerequisite(models.Model):
    """Model representing course prerequisites"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='required_prerequisites')
    prerequisite = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='required_for_courses')
    is_mandatory = models.BooleanField(default=True)
    minimum_grade = models.CharField(max_length=2, blank=True, null=True, 
                                   help_text="Minimum required grade if applicable")

    class Meta:
        unique_together = ['course', 'prerequisite']

    def __str__(self):
        return f"{self.course.code} requires {self.prerequisite.code}"

class ProgramCurriculum(models.Model):
    """Model linking programs to their required courses"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='curriculum')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='in_programs')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], 
                                 help_text="Semester when this course is typically taken")
    is_required = models.BooleanField(default=True)
    credits_contribution = models.IntegerField(help_text="Credits this course contributes to the program")

    class Meta:
        unique_together = ['program', 'course']
        ordering = ['program', 'semester', 'course']
        verbose_name_plural = "Program curricula"

    def __str__(self):
        return f"{self.program.code} - {self.course.code} (Semester {self.semester})"

class Semester(models.Model):
    """Model representing academic semesters"""
    name = models.CharField(max_length=50, help_text="e.g., Fall 2023, Spring 2024")
    code = models.CharField(max_length=20, unique=True, help_text="e.g., F2023, S2024")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    registration_start = models.DateField(help_text="When course registration begins")
    registration_end = models.DateField(help_text="When course registration ends")
    add_drop_deadline = models.DateField(help_text="Last day to add/drop courses")

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        # Ensure only one semester is marked as current
        if self.is_current:
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

class CourseOffering(models.Model):
    """Model representing a specific offering of a course in a semester"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='course_offerings')
    section = models.CharField(max_length=10, default='A', help_text="Section identifier")
    capacity = models.IntegerField(default=30)
    enrolled = models.IntegerField(default=0)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'lecturer'},
        related_name='taught_courses'
    )
    room = models.CharField(max_length=50, blank=True, null=True)
    schedule = models.TextField(blank=True, null=True, help_text="Class schedule details")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['course', 'semester', 'section']
        ordering = ['semester', 'course', 'section']

    def __str__(self):
        return f"{self.course.code} - {self.section} ({self.semester.code})"

    def available_seats(self):
        return self.capacity - self.enrolled

    def is_full(self):
        return self.enrolled >= self.capacity

class Enrollment(models.Model):
    """Model representing student enrollment in courses"""
    GRADE_CHOICES = (
        ('A', 'A (Excellent)'),
        ('B', 'B (Good)'),
        ('C', 'C (Satisfactory)'),
        ('D', 'D (Pass)'),
        ('F', 'F (Fail)'),
        ('W', 'W (Withdrawn)'),
        ('I', 'I (Incomplete)'),
        ('IP', 'IP (In Progress)'),
        ('', 'No Grade Yet'),
    )
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               limit_choices_to={'role': 'student'},
                               related_name='enrollments')
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, 
                                      related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='registered', 
                            choices=[('registered', 'Registered'),
                                    ('completed', 'Completed'),
                                    ('withdrawn', 'Withdrawn'),
                                    ('failed', 'Failed')])
    credits_earned = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'course_offering']
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student.username} - {self.course_offering.course.code}"

    def save(self, *args, **kwargs):
        # Update enrolled count in course offering
        if self.is_active and self.pk is None:
            self.course_offering.enrolled += 1
            self.course_offering.save()
        super().save(*args, **kwargs)

class ProgramEnrollment(models.Model):
    """Model representing student enrollment in programs"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='program_enrollments'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrollment_date = models.DateField(default=timezone.now)  # ✅ fixed
    expected_graduation = models.DateField()
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        default='active',
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('suspended', 'Suspended'),
            ('withdrawn', 'Withdrawn'),
        ]
    )
    current_semester = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ['student', 'program']
        ordering = ['-enrollment_date']  # ✅ now works

    def __str__(self):
        return f"{self.student.username} - {self.program.code}"

    def credits_completed(self):
        completed_enrollments = Enrollment.objects.filter(
            student=self.student,
            course_offering__course__in=self.program.curriculum.all().values('course'),
            status='completed'
        )
        return sum(
            enrollment.credits_earned or enrollment.course_offering.course.credits
            for enrollment in completed_enrollments
        )

    def progress_percentage(self):
        if self.program.total_credits > 0:
            return (self.credits_completed() / self.program.total_credits) * 100
        return 0
    
    


class FinanceRecord(models.Model):
    TRANSACTION_TYPES = (
        ('fee', 'Fee Charge'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='finance_records'
    )
    program = models.ForeignKey(
        'Program',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finance_records',
        help_text="Program associated with this transaction"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Remaining balance after this transaction",
        editable=False
    )
    transaction_date = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']  # Use ID to preserve insertion order

    def __str__(self):
        return f"{self.student.username} - {self.transaction_type} - {self.amount}"

    def save(self, *args, **kwargs):
        # Total program fee
        program_total_fee = self.program.total_program_fee() if self.program else Decimal('0.00')

        # Sum of previous payments (for the same student & program)
        previous_payments = FinanceRecord.objects.filter(
            student=self.student,
            program=self.program
        ).exclude(pk=self.pk)  # exclude current record if updating

        total_paid = sum(
            r.amount if r.transaction_type in ('payment', 'refund') else -r.amount
            for r in previous_payments
        )

        # Calculate remaining balance
        if self.transaction_type in ('payment', 'refund'):
            total_paid += self.amount
        elif self.transaction_type in ('fee', 'adjustment'):
            total_paid -= self.amount

        self.balance_after = program_total_fee - total_paid

        super().save(*args, **kwargs)



class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='assignments/') 
    due_date = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'lecturer'} 
    )

    def __str__(self):
        return self.title
    
    
    
class Event(models.Model):
    Event_TYPES = [
        ('accademic', 'Accademic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('others','Others')
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    event_type = models.CharField(max_length=10, choices=Event_TYPES,default='others')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    