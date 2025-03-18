from django.contrib import admin
from .models import Student, Course, Instructor, Enrollment, Fee, StudentFee, Payment, Schedule, Attendance, SentEmail

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('amount', 'date', 'transaction_id')

class StudentFeeInline(admin.TabularInline):
    model = StudentFee
    extra = 0
    readonly_fields = ('total_fee', 'total_paid', 'remaining_balance')

class FeeInline(admin.TabularInline):
    model = Fee
    extra = 1

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty', 'major', 'student_id', 'university_email', 'registration_date')
    search_fields = ('name', 'student_id', 'university_email')
    list_filter = ('faculty', 'major')
    inlines = [EnrollmentInline, PaymentInline, StudentFeeInline]
    ordering = ('name',)

    def delete_model(self, request, obj):
        # Ensure that related payments are also deleted
        Payment.objects.filter(student=obj).delete()
        super().delete_model(request, obj)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'credit_hours', 'instructor')
    search_fields = ('name', 'code')
    list_filter = ('credit_hours',)
    inlines = [FeeInline, ScheduleInline]
    ordering = ('name',)

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'department', 'enrolled_students')
    search_fields = ('full_name', 'email')
    list_filter = ('department',)
    ordering = ('full_name',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('get_student_name', 'get_course_name', 'get_instructor_name')
    search_fields = ('student__name', 'course__name', 'instructor__full_name')
    list_filter = ('course', 'instructor')
    ordering = ('student__name',)

    def delete_model(self, request, obj):
        # Ensure that related payments are also deleted
        Payment.objects.filter(student=obj.student).delete()
        super().delete_model(request, obj)

    def get_student_name(self, obj):
        return obj.student.name
    get_student_name.short_description = 'Student'
    get_student_name.admin_order_field = 'student__name'

    def get_course_name(self, obj):
        return obj.course.name
    get_course_name.short_description = 'Course'
    get_course_name.admin_order_field = 'course__name'

    def get_instructor_name(self, obj):
        return obj.instructor.full_name
    get_instructor_name.short_description = 'Instructor'
    get_instructor_name.admin_order_field = 'instructor__full_name'

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('course', 'amount')
    search_fields = ('course__name',)
    list_filter = ('amount',)
    ordering = ('course__name',)

@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_fee', 'total_paid', 'remaining_balance')
    readonly_fields = ('total_fee', 'total_paid', 'remaining_balance')
    search_fields = ('student__name', 'student__student_id', 'student__university_email')
    list_filter = ('student__faculty', 'student__major')
    ordering = ('student__name',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'date', 'transaction_id')
    search_fields = ('student__name', 'transaction_id')
    list_filter = ('date',)
    ordering = ('date',)

    # Ensure that the admin can delete payment objects
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('course__name',)
    list_filter = ('day_of_week',)
    ordering = ('course__name',)

admin.site.register(Attendance)
admin.site.register(SentEmail)