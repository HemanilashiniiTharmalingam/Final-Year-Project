from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from .forms import RegistrationForm, CustomLoginForm, AnnouncementForm, SetPasswordForm, EnrollmentForm, PaymentForm, AssignmentForm, AssignmentSubmissionForm, EmailForm, GradeForm, AttendanceForm
from .models import Instructor, Course, Assignment, Announcement, Student, Enrollment, StudentFee, Payment, Grade, AssignmentSubmission, Notification, SentEmail, Schedule, Attendance
import uuid

#########################################################################################################
                                        #REGISTER_OR_LOGIN#
#########################################################################################################

@csrf_protect
def register_or_login(request):
    registration_form = RegistrationForm()
    login_form = CustomLoginForm()
    set_password_form = SetPasswordForm()

    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'register':
            registration_form = RegistrationForm(request.POST)
            if registration_form.is_valid():
                username = registration_form.cleaned_data.get('username')
                email = registration_form.cleaned_data.get('email')
                password = registration_form.cleaned_data.get('password1')  
                student_exists = Student.objects.filter(university_email=email).exists()
                instructor_exists = Instructor.objects.filter(email=email).exists()

                if student_exists or instructor_exists:
                    try:
                        user = User.objects.get(username=username)
                        messages.error(request, 'This username is already registered. Please log in.')
                    except User.DoesNotExist:
                        user = User.objects.create_user(username=username, password=password, email=email)
                        user.save()
                        if student_exists:
                            student = Student.objects.get(university_email=email)
                            student.user = user
                            student.save()
                        elif instructor_exists:
                            instructor = Instructor.objects.get(email=email)
                            instructor.user = user
                            instructor.save()
                        messages.success(request, 'User created successfully. You can now log in.')
                else:
                    messages.error(request, 'Email not found. Please contact the administrator.')

            else:
                messages.error(request, 'Registration failed. Please check the details and try again.')

        elif 'action' in request.POST and request.POST['action'] == 'login':
            login_form = CustomLoginForm(request, data=request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    if Student.objects.filter(university_email=user.email).exists():
                        try:
                            student = Student.objects.get(university_email=user.email)
                            messages.success(request, 'Logged in successfully.')
                            return redirect('student_dashboard', student_id=student.id)
                        except Student.DoesNotExist:
                            messages.error(request, 'Student not found. Please contact the administrator.')
                    elif Instructor.objects.filter(email=user.email).exists():
                        try:
                            instructor = Instructor.objects.get(email=user.email)
                            messages.success(request, 'Logged in successfully.')
                            return redirect('instructor_dashboard')
                        except Instructor.DoesNotExist:
                            messages.error(request, 'Instructor not found. Please contact the administrator.')
                    else:
                        messages.error(request, 'User type not found. Please contact the administrator.')
                else:
                    messages.error(request, 'Invalid university email or password.')
            else:
                messages.error(request, 'Invalid university email or password.')

    return render(request, 'pro/register_or_login.html', {
        'registration_form': registration_form,
        'login_form': login_form,
        'set_password_form': set_password_form,
    })

    
#########################################################################################################
                                        #STUDENT#
#########################################################################################################


@csrf_protect
@login_required(login_url='/')
def student_dashboard(request, student_id):
    print("student_dashboard view called") 
    student = get_object_or_404(Student, id=student_id)
    enrollments = Enrollment.objects.filter(student=student)
    courses = [enrollment.course for enrollment in enrollments]
    instructors = Instructor.objects.filter(course__in=courses).distinct()
    schedules = Schedule.objects.filter(course__in=courses)

    student_fee, created = StudentFee.objects.get_or_create(student=student)
    if not student_fee:
        raise AttributeError("StudentFee object could not be created or retrieved.")

    payments = Payment.objects.filter(student=student)
    total_paid = student_fee.total_paid
    remaining_balance = student_fee.remaining_balance
    grades = Grade.objects.filter(student=student)
    assignments = Assignment.objects.filter(course__in=courses).distinct().select_related('instructor')
    submissions = AssignmentSubmission.objects.filter(student=student)
    submitted_assignment_ids = submissions.values_list('assignment_id', flat=True)
    notifications = Notification.objects.filter(student=student).order_by('-created_at')
    student_sent_emails = SentEmail.objects.filter(sender_student=student).order_by('-sent_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        print("POST request received")
        action = request.POST.get('action')
        print(f"Action received: {action}")

        if action == 'send_email':
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                recipient_email = email_form.cleaned_data['recipient_email']
                subject = email_form.cleaned_data['subject']
                message = email_form.cleaned_data['message']

                try:
                    send_mail(subject, message, f"{student.name} <{student.university_email}>", [recipient_email])
                except Exception as e:
                    messages.error(request, 'Failed to send email.')
                    return redirect('student_dashboard', student_id=student.id)

                recipient_student = Student.objects.filter(university_email=recipient_email).first()
                recipient_instructor = Instructor.objects.filter(email=recipient_email).first()

                sent_email = SentEmail.objects.create(
                    sender_student=student,
                    recipient_student=recipient_student,
                    recipient_instructor=recipient_instructor,
                    recipient_email=recipient_email,
                    subject=subject,
                    message=message,
                    sent_at=timezone.now()
                )

                if recipient_student:
                    Notification.objects.create(
                        student=recipient_student,
                        subject=f'Email from {student.name}',
                        message=message,
                        created_at=timezone.now()
                    )
                elif recipient_instructor:
                    Notification.objects.create(
                        instructor=recipient_instructor,
                        subject=f'Email from {student.name}',
                        message=message,
                        created_at=timezone.now()
                    )

                messages.success(request, 'Email sent successfully!')
                return redirect('student_dashboard', student_id=student.id)
            else:
                messages.error(request, 'Invalid form data.')

        elif action == 'delete_email':
            email_id = request.POST.get('email_id')
            sent_email = get_object_or_404(SentEmail, id=email_id)
            sent_email.delete()
            messages.success(request, 'Email deleted successfully.')
            return redirect('student_dashboard', student_id=student.id)

        elif 'mark_notification_read' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, student=student)
            notification.is_read = True
            notification.save()
            messages.success(request, 'Notification marked as read.')
            return redirect('student_dashboard', student_id=student.id)

        elif 'delete_notification' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, student=student)
            notification.delete()
            messages.success(request, 'Notification deleted successfully.')
            return redirect('student_dashboard', student_id=student.id)

        form = EnrollmentForm(request.POST, student=student)
        payment_form = PaymentForm(request.POST, student_fee=student_fee)
        assignment_form = AssignmentSubmissionForm(request.POST, request.FILES)
        email_form = EmailForm(request.POST)

        if 'enroll' in request.POST:
            print(f"Enrollment form data: {form.data}")
            if form.is_valid():
                print("Enrollment form is valid.")
                enrollment = form.save(commit=False)
                enrollment.student = student
                enrollment.instructor = enrollment.course.instructor
                enrollment.save()
                student_fee.save()  # Update StudentFee after new enrollment
                messages.success(request, 'Enrollment successful!')
                return redirect('student_dashboard', student_id=student.id)
            else:
                print(f"Enrollment form errors: {form.errors}")  # Debugging statement
                messages.error(request, 'Enrollment form is not valid.')
            
        elif 'pay' in request.POST:
            if payment_form.is_valid():
                payment = payment_form.save(commit=False)
                payment.student = student
                payment.transaction_id = str(uuid.uuid4())
                payment.save()
                student_fee.save()  # Update StudentFee after payment
                return redirect('student_dashboard', student_id=student.id)
            
        elif 'submit_assignment' in request.POST:
            assignment_id = request.POST.get('assignment_id')
            assignment = get_object_or_404(Assignment, id=assignment_id)
            if assignment_form.is_valid():
                submission = assignment_form.save(commit=False)
                submission.assignment = assignment
                submission.student = student
                submission.save()
                messages.success(request, 'Assignment submitted successfully!')
                return redirect('student_dashboard', student_id=student.id)
            
        elif 'delete_assignment' in request.POST:
            assignment_id = request.POST.get('assignment_id')
            assignment = get_object_or_404(Assignment, id=assignment_id)
            assignment.delete()
            messages.success(request, 'Assignment deleted successfully!')
            return redirect('student_dashboard', student_id=student.id)
        
    else:
        form = EnrollmentForm(student=student)
        payment_form = PaymentForm(student_fee=student_fee)
        assignment_form = AssignmentSubmissionForm()
        email_form = EmailForm()

    context = {
        'student': student,
        'courses': courses,
        'instructors': instructors,
        'total_fee': student_fee.total_fee,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'form': form,
        'payment_form': payment_form,
        'assignment_form': assignment_form,
        'email_form': email_form,
        'payments': payments,
        'grades': grades,
        'assignments': assignments,
        'submitted_assignment_ids': list(submitted_assignment_ids),  # Convert to list for template use
        'notifications': notifications,
        'schedules': schedules,
        'student_sent_emails': student_sent_emails,  # Include student sent emails in context
    }
    return render(request, 'pro/student_dashboard.html', context)



#########################################################################################################
                                        #INSTRUCTOR#
#########################################################################################################


@csrf_protect
@login_required(login_url='/')
def instructor_dashboard(request):
    instructor = get_object_or_404(Instructor, email=request.user.email)
    courses = Course.objects.filter(instructor=instructor)
    schedules = Schedule.objects.filter(course__in=courses)
    enrollments = Enrollment.objects.filter(course__in=courses).select_related('student', 'course')
    assignments = Assignment.objects.filter(instructor=instructor)
    announcements = Announcement.objects.filter(instructor=instructor)
    sent_emails = SentEmail.objects.filter(sender_instructor=instructor).order_by('-sent_at')
    notifications = Notification.objects.filter(instructor=instructor).order_by('-created_at').distinct()
    grades = Grade.objects.filter(course__in=courses).select_related('student', 'course')
    assignment_submissions = AssignmentSubmission.objects.filter(assignment__in=assignments).select_related('assignment', 'student')

    assignment_form = AssignmentForm()
    announcement_form = AnnouncementForm()
    email_form = EmailForm()
    grade_form = GradeForm(instructor=instructor)
    attendance_form = AttendanceForm(instructor=instructor)
    attendance_records = Attendance.objects.filter(course__in=courses).select_related('student', 'course', 'schedule')

    students = Student.objects.filter(enrollment__course__in=courses).distinct()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_email':
            email_form = EmailForm(request.POST)
            if email_form.is_valid():
                recipient_email = email_form.cleaned_data['recipient_email']
                subject = email_form.cleaned_data['subject']
                message = email_form.cleaned_data['message']

                try:
                    send_mail(subject, message, f"{instructor.full_name} <{instructor.email}>", [recipient_email])
                except Exception as e:
                    messages.error(request, f'Failed to send email: {e}')
                    return redirect('instructor_dashboard')

                recipient_student = Student.objects.filter(university_email=recipient_email).first()
                recipient_instructor = Instructor.objects.filter(email=recipient_email).first()

                sent_email = SentEmail.objects.create(
                    sender_instructor=instructor,
                    recipient_student=recipient_student,
                    recipient_instructor=recipient_instructor,
                    recipient_email=recipient_email,
                    subject=subject,
                    message=message,
                    sent_at=timezone.now()
                )

                if recipient_student:
                    Notification.objects.create(
                        student=recipient_student,
                        subject=f'Email from {instructor.full_name}',
                        message=message,
                        created_at=timezone.now()
                    )
                elif recipient_instructor:
                    Notification.objects.create(
                        instructor=recipient_instructor,
                        subject=f'Email from {instructor.full_name}',
                        message=message,
                        created_at=timezone.now()
                    )

                messages.success(request, 'Email sent successfully!')
                return redirect('instructor_dashboard')
            else:
                messages.error(request, 'Invalid form data.')

        elif action == 'delete_email':
            email_id = request.POST.get('email_id')
            sent_email = get_object_or_404(SentEmail, id=email_id)
            sent_email.delete()
            messages.success(request, 'Email deleted successfully!')
            return redirect('instructor_dashboard')

        elif 'make_announcement' in request.POST:
            announcement_form = AnnouncementForm(request.POST)
            if announcement_form.is_valid():
                new_announcement = announcement_form.save(commit=False)
                new_announcement.instructor = instructor
                new_announcement.save()

                for enrollment in enrollments:
                    Notification.objects.create(
                        student=enrollment.student,
                        subject='New Announcement',
                        message=new_announcement.content,
                        created_at=timezone.now()
                    )

                messages.success(request, 'Announcement made successfully!')
                return redirect('instructor_dashboard')
            else:
                messages.error(request, 'Error in making announcement.')

        elif action == 'delete_announcement':
            announcement_id = request.POST.get('announcement_id')
            announcement = get_object_or_404(Announcement, id=announcement_id, instructor=instructor)
            announcement.delete()
            messages.success(request, 'Announcement deleted successfully!')
            return redirect('instructor_dashboard')

        elif 'add_assignment' in request.POST:
            assignment_form = AssignmentForm(request.POST, request.FILES)
            if assignment_form.is_valid():
                new_assignment = assignment_form.save(commit=False)
                new_assignment.instructor = instructor
                new_assignment.save()
                messages.success(request, 'Assignment added successfully!')
                return redirect('instructor_dashboard')
            else:
                messages.error(request, 'Error in adding assignment.')

        elif 'delete_assignment' in request.POST:
            assignment_id = request.POST.get('assignment_id')
            assignment = get_object_or_404(Assignment, id=assignment_id, instructor=instructor)
            assignment.delete()
            messages.success(request, 'Assignment deleted successfully!')
            return redirect('instructor_dashboard')

        elif 'update_grade' in request.POST:
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            grade_value = request.POST.get('grade')
            grade, created = Grade.objects.get_or_create(student_id=student_id, course_id=course_id)
            grade.grade = grade_value
            grade.save()
            messages.success(request, 'Grade updated successfully!')
            return redirect('instructor_dashboard')

        elif 'add_grade' in request.POST:
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            grade_value = request.POST.get('grade')
            student = get_object_or_404(Student, id=student_id)
            course = get_object_or_404(Course, id=course_id)
            Grade.objects.update_or_create(student=student, course=course, defaults={'grade': grade_value})
            messages.success(request, 'Grade added/updated successfully!')
            return redirect('instructor_dashboard')

        elif 'delete_grade' in request.POST:
            student_id = request.POST.get('student_id')
            course_id = request.POST.get('course_id')
            Grade.objects.filter(student_id=student_id, course_id=course_id).delete()
            messages.success(request, 'Grade deleted successfully!')
            return redirect('instructor_dashboard')

        elif 'mark_notification_read' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, instructor=instructor)
            notification.is_read = True
            notification.save()
            messages.success(request, 'Notification marked as read!')
            return redirect('instructor_dashboard')

        elif 'delete_notification' in request.POST:
            notification_id = request.POST.get('notification_id')
            notification = get_object_or_404(Notification, id=notification_id, instructor=instructor)
            notification.delete()
            messages.success(request, 'Notification deleted successfully.')
            return redirect('instructor_dashboard')

        elif 'mark_attendance' in request.POST:
            attendance_form = AttendanceForm(request.POST, instructor=instructor)
            if attendance_form.is_valid():
                course = attendance_form.cleaned_data['course']
                schedule = attendance_form.cleaned_data['schedule']
                date = attendance_form.cleaned_data['date']
                status = attendance_form.cleaned_data['status']
                students = attendance_form.cleaned_data['students']

                for student in students:
                    Attendance.objects.create(
                        student=student,
                        course=course,
                        schedule=schedule,
                        date=date,
                        status=status
                    )

                messages.success(request, 'Attendance marked successfully!')
                return redirect('instructor_dashboard')
            else:
                messages.error(request, 'Error in marking attendance.')

    context = {
        'instructor': instructor,
        'enrollments': enrollments,
        'courses': courses,
        'assignments': assignments,
        'announcements': announcements,
        'sent_emails': sent_emails,
        'schedules': schedules,
        'notifications': notifications,
        'grades': grades,
        'assignment_submissions': assignment_submissions,
        'announcement_form': announcement_form,
        'assignment_form': assignment_form,
        'email_form': email_form,
        'grade_form': grade_form,
        'attendance_form': attendance_form,
        'attendance_records': attendance_records,
        'students': students,
    }

    return render(request, 'pro/instructor_dashboard.html', context)






