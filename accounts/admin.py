from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, LecturerProfile

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'registration_number', 'phone_number', 'profile_picture')
        }),
    )
    list_display = ('username', 'email', 'role', 'registration_number', 'phone_number')
    search_fields = ('username', 'email', 'registration_number', 'phone_number')

admin.site.register(User, UserAdmin)
admin.site.register(StudentProfile)
admin.site.register(LecturerProfile)
