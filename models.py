from django.db import models
import uuid
from django.utils.html import format_html
from django.utils import timezone


#########################################################################################################################################################
#########################################################################################################################################################


class Student(models.Model):
    name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name='Date of Birth')
    faculty = models.CharField(max_length=100)
    major = models.CharField(max_length=100, null=True, blank=True)
    student_id = models.CharField(max_length=10, blank=True, unique=True, editable=False)
    university_email = models.EmailField(blank=True, null=True, unique=True)
    registration_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Student.objects.get(pk=self.pk)
            major_changed = orig.major != self.major
        else:
            major_changed = True

        if major_changed and self.major:
            random_part = str(uuid.uuid4())[:4]
            major_part = ''.join(e for e in self.major if e.isalnum())[:3].upper()
            self.student_id = f"{major_part}{random_part}"
            self.university_email = f"{self.student_id}@stu.uni.edu"

        super(Student, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Instructor(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

    def enrolled_students(self):
        enrollments = self.enrollments.all()
        if not enrollments:
            return "No students enrolled"
        rows = ''.join(
            f"<tr><td>{enrollment.student.name}</td><td>{enrollment.student.student_id}</td><td>{enrollment.student.university_email}</td></tr>"
            for enrollment in enrollments
        )
        table = f"<table><thead><tr><th>Name</th><th>ID</th><th>Email</th></tr></thead><tbody>{rows}</tbody></table>"
        return format_html(table)

    enrolled_students.short_description = "Students Enrolled"

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    credit_hours = models.IntegerField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='enrollments')

    def __str__(self):
        return f"{self.student.name} enrolled in {self.course.name} under {self.instructor.full_name}"

class Fee(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Fee for {self.course.name}: {self.amount}"

class StudentFee(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='student_fee')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def total_fee(self):
        return sum(fee.amount for fee in Fee.objects.filter(course__enrollment__student=self.student))

    @property
    def total_paid(self):
        return sum(payment.amount for payment in Payment.objects.filter(student=self.student))

    @property
    def remaining_balance(self):
        return self.total_fee - self.total_paid

    def __str__(self):
        return f"Total fee for {self.student.name}"

class Assignment(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    reference_document = models.FileField(upload_to='assignments/', null=True, blank=True)

    def __str__(self):
        return self.title
 
class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submission_file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Payment of {self.amount} by {self.student.name} on {self.date}"

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2)

    def __str__(self):
        return f'{self.student.name} - {self.course.name} - {self.grade}'

class SentEmail(models.Model):
    sender_student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_emails')
    sender_instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_emails')
    recipient_student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='received_emails')
    recipient_instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True, related_name='received_emails')
    recipient_email = models.EmailField(null=True, blank=True)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.sent_at}"
    
class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.created_at}"


class Schedule(models.Model):
    DAY_OF_WEEK_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.course.name} on {self.get_day_of_week_display()} from {self.start_time} to {self.end_time}"
    
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')])

    def __str__(self):
        return f"{self.student} - {self.course} - {self.schedule} - {self.date} - {self.status}"