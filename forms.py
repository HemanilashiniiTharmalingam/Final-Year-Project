from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Student, Instructor, Announcement, Enrollment, SentEmail, Grade, Course, Payment, AssignmentSubmission, Assignment, Schedule, Attendance

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='University Email', max_length=254, widget=forms.EmailInput)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class SetPasswordForm(forms.Form):
    email = forms.EmailField(label='University Email', max_length=254)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")

        return cleaned_data
    
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']


class EnrollmentForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.all(), empty_label="Select a course")

    class Meta:
        model = Enrollment
        fields = ['course']

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            self.fields['course'].queryset = Course.objects.exclude(enrollment__student=student)


GRADE_CHOICES = [
    ('None', 'None'),
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('F', 'F'),
]

class GradeForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.none())
    student = forms.ModelChoiceField(queryset=Student.objects.none())
    grade = forms.ChoiceField(choices=GRADE_CHOICES)

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop('instructor', None)
        super(GradeForm, self).__init__(*args, **kwargs)
        if instructor:
            self.fields['course'].queryset = Course.objects.filter(instructor=instructor)
            self.fields['student'].queryset = Student.objects.filter(enrollment__course__in=instructor.course_set.all()).distinct()

    class Meta:
        model = Grade
        fields = ['student', 'course', 'grade']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount']

    def __init__(self, *args, **kwargs):
        self.student_fee = kwargs.pop('student_fee', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        total_fee = self.student_fee.total_fee
        paid_amount = self.student_fee.total_paid
        if amount + paid_amount > total_fee:
            raise forms.ValidationError(f"Payment amount exceeds the total fee. You have {total_fee - paid_amount} remaining.")
        return amount

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'course', 'reference_document']

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file']

class EmailForm(forms.Form):
    recipient_email = forms.EmailField(
        label="Recipient Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    subject = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))


class ScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['course', 'day_of_week', 'start_time', 'end_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for day_of_week, start_time, and end_time
        if not self.instance.pk:  # Only set defaults if this is a new instance
            self.fields['day_of_week'].initial = 0  # Monday
            self.fields['start_time'].initial = '09:00:00'
            self.fields['end_time'].initial = '10:00:00'

class AttendanceForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(queryset=Student.objects.none(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Attendance
        fields = ['course', 'schedule', 'date', 'status']

    def __init__(self, *args, **kwargs):
        instructor = kwargs.pop('instructor', None)
        super().__init__(*args, **kwargs)
        if instructor:
            self.fields['course'].queryset = Course.objects.filter(instructor=instructor)
            self.fields['schedule'].queryset = Schedule.objects.filter(course__in=Course.objects.filter(instructor=instructor))
            self.fields['students'].queryset = Student.objects.filter(enrollment__course__in=Course.objects.filter(instructor=instructor)).distinct()