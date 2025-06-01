# mtc_checker/views.py

# Django Core
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Count, Avg, Max
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views

# Python Standard Library
import json
import csv
import io
from django.shortcuts import redirect
from django.urls import reverse

# Your App's Modules
from .models import Student, TestAttempt
from .forms import StudentForm, CSVUploadForm, StudentLoginForm, StudentCreationForm  # Include StudentLoginForm
from .question_generator import MTCQuestionGenerator

# Django Authentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User  #Import User model


# --- Helper Function for Admin View Protection ---
def is_staff_user(user):
    return user.is_authenticated and user.is_staff


# --- Public/Student Facing Views ---

def student_login_or_select_view(request):
    students = Student.objects.all().order_by('last_name', 'first_name')
    if not students:
        return render(request, 'mtc_checker/no_students.html')
    return render(request, 'mtc_checker/student_select.html', {'students': students})


def test_interface_view(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    generator = MTCQuestionGenerator()
    test_set = generator.get_full_test_set()

    context = {
        'student': student,
        'practice_questions_json': json.dumps(test_set['practice']),
        'main_questions_json': json.dumps(test_set['main']),
        'num_total_main_questions': generator.NUM_QUESTIONS,
        'app_name': 'mtc_checker'
    }
    return render(request, 'mtc_checker/test_interface.html', context)


@csrf_exempt
@require_POST
def submit_test_view(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    try:
        data = json.loads(request.body)
        score = data.get('score')
        total_questions = data.get('total_questions', 25)  # Default if not provided
        answered_questions_data = data.get('answered_questions', [])

        if score is None:
            return JsonResponse({'status': 'error', 'message': 'Score not provided'}, status=400)

        attempt = TestAttempt.objects.create(
            student=student,
            score=score,
            total_questions=total_questions,
            test_data={'answered_questions': answered_questions_data}
        )
        # NEW CODE ADDED HERE
        return redirect(reverse('mtc_checker:test_complete', kwargs={'student_id': student_id, 'attempt_id': str(attempt.id)}))
        # NEW CODE
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in submit_test_view: {e}")
        return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)


def test_complete_view(request, student_id, attempt_id):
    student = get_object_or_404(Student, student_id=student_id)
    attempt = get_object_or_404(TestAttempt, id=attempt_id, student=student)
    context = {
        'student': student,
        'attempt': attempt,
        'app_name': 'mtc_checker'
    }
    return render(request, 'mtc_checker/test_complete.html', context)


def student_login_view(request):
    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                try:
                    student = Student.objects.get(user=user)
                    return redirect(reverse('mtc_checker:test_interface', kwargs={'student_id': student.student_id}))
                except Student.DoesNotExist:
                     messages.error(request, "Student is not setup correctly. Contact admin")
                     return render(request, 'mtc_checker/student_login.html', {'form': form})

            else:
                messages.error(request, "Invalid username or password.")
        else:
            print("Error at student login", form.errors)
    else:
        form = StudentLoginForm()
    return render(request, 'mtc_checker/student_login.html', {'form': form})


@login_required  # Login required for test
def test_results_view(request, student_id):
    # Ensure the user matches the student id to secure results page
    student = get_object_or_404(Student, student_id=student_id, user=request.user)
    return render(request, 'mtc_checker/student_results.html', {'student_id': student_id})


@login_required  # Login required for test
def student_results_view(request, student_id):
    student = get_object_or_404(Student, student_id=student_id, user=request.user)  # Ensure the user matches the student id to secure results page

    # Fetch summary data for the student (similar to your original test_results_view)
    students_summary = Student.objects.annotate(
        num_tests=Count('test_attempts'),
        average_score=Avg('test_attempts__score'),
        latest_test_timestamp=Max('test_attempts__timestamp')
    ).filter(student_id=student_id)

    # Fetch detailed progress data for the student (for the chart)
    student_progress_data = {}
    for student_summary in students_summary:
        attempts = TestAttempt.objects.filter(student=student_summary).order_by('timestamp')
        student_progress_data[str(student_summary.student_id)] = {
            'labels': [attempt.timestamp.strftime("%b %d, %H:%M") for attempt in attempts],
            'scores': [attempt.score for attempt in attempts],
            'total_questions': [attempt.total_questions for attempt in attempts]
        }

    context = {
        'student': student,  # Pass the student object to the template
        'students_summary': students_summary,
        'student_progress_data_json': json.dumps(student_progress_data),
    }
    return render(request, 'mtc_checker/student_results.html', context)  # Render the new template

# --- Custom Admin Views for Student Management ---

@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_admin_dashboard_view(request):
    students = Student.objects.all().order_by('last_name', 'first_name')
    # Generate URLs for each student's results page
    for student in students:
        student.results_url = reverse('mtc_checker:test_results', args=[student.student_id])

    context = {
        'students': students,
        'page_title': 'Student Management'
    }
    return render(request, 'mtc_checker/admin/student_list_manage.html', context)

@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_add_view(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Student '{user.username}' and user created successfully.")
            return redirect('mtc_checker:student_admin_dashboard')
        else:
            messages.error(request, "User creation failed. Please correct the errors below.")

    else:
        form = StudentCreationForm()
    return render(request, 'mtc_checker/admin/student_form.html', {'form': form, 'page_title': 'Add New Student'})


@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_edit_view(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.first_name} {student.last_name}' updated successfully.")
            return redirect('mtc_checker:student_admin_dashboard')
    else:
        form = StudentForm(instance=student)
    context = {
        'form': form,
        'student': student,  # Pass student for context if needed in template
        'page_title': f'Edit Student: {student.first_name} {student.last_name}'
    }
    return render(request, 'mtc_checker/admin/student_form.html', context)


@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_delete_view(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    # It's good practice to have a confirmation page for GET requests
    # and perform deletion on POST.
    if request.method == 'POST':
        student_name = f"{student.first_name} {student.last_name}"  # Get name before deleting
        student.delete()
        messages.success(request, f"Student '{student_name}' deleted successfully.")
        return redirect('mtc_checker:student_admin_dashboard')

    # For GET request, show a confirmation template (or rely on JS confirm in list_manage)
    # If you have a student_confirm_delete.html template:
    # context = {'student': student, 'page_title': 'Confirm Deletion'}
    # return render(request, 'mtc_checker/admin/student_confirm_delete.html', context)
    # For now, assuming POST only from a JS confirm. If not, add GET handling.
    # If the form in student_list_manage.html directly POSTs here, this is fine.
    messages.warning(request, "Deletion must be confirmed via POST.")  # Should not be reached if form is POST
    return redirect('mtc_checker:student_admin_dashboard')


@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_upload_csv_view(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file. Please upload a valid .csv file.')
                return redirect('mtc_checker:student_admin_dashboard')

            try:
                decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                reader = csv.DictReader(decoded_file)

                created_count = 0
                updated_count = 0  # If you implement updates
                errors = []

                for row_num, row in enumerate(reader, 1):
                    first_name = row.get('FirstName') or row.get('first_name')
                    last_name = row.get('LastName') or row.get('last_name')

                    if not first_name or not last_name:
                        errors.append(f"Row {row_num}: Missing FirstName or LastName.")
                        continue

                    try:
                        student, created = Student.objects.get_or_create(
                            first_name=first_name.strip(),
                            last_name=last_name.strip(),
                            # Add defaults for other required fields if any from your Student model
                        )
                        if created:
                            created_count += 1
                        else:
                            # Logic for updating the existing student if needed
                            # student.some_other_field = row.get('SomeOtherField', student.some_other_field)
                            # student.save()
                            updated_count += 1  # Count as updated if found

                    except Exception as e:
                        errors.append(f"Row {row_num} ('{first_name} {last_name}'): Error - {str(e)}")

                if errors:
                    for error_msg in errors:
                        messages.warning(request, error_msg)

                success_msg_parts = []
                if created_count > 0:
                    success_msg_parts.append(f"{created_count} new student(s) uploaded")
                if updated_count > 0 and created_count == 0:  # Only mention update if no new ones, or adjust wording
                    success_msg_parts.append(f"{updated_count} student(s) found (already existed or updated)")
                elif updated_count > 0:
                    success_msg_parts.append(f"and {updated_count} existing student(s) processed")

                if success_msg_parts:
                    messages.success(request, f"{' '.join(success_msg_parts)} successfully.")
                elif not errors:  # No new, no updates, no errors
                    messages.info(request, "CSV processed. No new students were added (they may already exist or CSV was empty).")

            except Exception as e:
                messages.error(request, f"Error processing CSV file: {str(e)}")

            return redirect('mtc_checker:student_admin_dashboard')
        else:  # Form not valid
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    messages.error(request, f"Upload error: {error} (field: {field})")
            return redirect('mtc_checker:student_admin_dashboard')

    else:  # GET request to this URL
        messages.error(request, "Please upload a CSV file using the form.")
        return redirect('mtc_checker:student_admin_dashboard')
@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_admin_dashboard_view(request):
    students = Student.objects.all().order_by('last_name', 'first_name')
    # Generate URLs for each student's results page
    for student in students:
        student.results_url = reverse('mtc_checker:test_results', args=[student.student_id])

    context = {
        'students': students,
        'page_title': 'Student Management'
    }
    return render(request, 'mtc_checker/admin/student_list_manage.html', context)
@user_passes_test(is_staff_user, login_url=reverse_lazy('admin:login'))
def student_add_view(request):
    if request.method == 'POST':
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Student '{user.username}' and user created successfully.")
            return redirect('mtc_checker:student_admin_dashboard')
        else:
            messages.error(request, "User creation failed. Please correct the errors below.")

    else:
        form = StudentCreationForm()
    return render(request, 'mtc_checker/admin/student_form.html', {'form': form, 'page_title': 'Add New Student'})