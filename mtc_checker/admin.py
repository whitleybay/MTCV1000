from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  # Correct import
from django.contrib.auth.models import User
from .models import Student

# Define an inline admin descriptor for Student model
# which acts a bit like a singleton
class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student'
    exclude = ('student_id',)

# Define a new User admin
class CustomUserAdmin(UserAdmin):
    inlines = (StudentInline,)  # Only keep this
    # list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    # list_filter = ('is_staff', 'is_superuser', 'is_active')
    # fieldsets = (
    #     (None, {'fields': ('username', 'password')}),
    #     ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
    #     ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
    #                                    'groups', 'user_permissions')}),
    #     ('Important dates', {'fields': ('last_login', 'date_joined')}),
    # )
#
#     def get_urls(self):
#         from django.urls import path
#         urls = super().get_urls()
#         custom_urls = [
#             path('upload-csv/', self.upload_csv, name='upload_csv'),
#         ]
#         return custom_urls + urls
#
#     def upload_csv(self, request):
#       if request.method == 'POST':
#         from .forms import CSVUploadForm
#         form = CSVUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#           csv_file = request.FILES['csv_file']
#           if not csv_file.name.endswith('.csv'):
#             self.message_user(request, 'This is not a CSV file. Please upload a valid .csv file.', level='ERROR')
#             return redirect(request.path)
#
#           try:
#               import csv
#               import io
#               decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8-sig')
#               reader = csv.DictReader(decoded_file)
#               created_count = 0
#               updated_count = 0
#               errors = []
#               for row_num, row in enumerate(reader, 1):
#                   first_name = row.get('FirstName') or row.get('first_name')
#                   last_name = row.get('LastName') or row.get('last_name')
#
#                   if not first_name or not last_name:
#                     errors.append(f"Row {row_num}: Missing FirstName or LastName.")
#                     continue
#
#                   try:
#                     user, user_created = User.objects.get_or_create(
#                         username=f"{first_name.lower()}.{last_name.lower()}",
#                         defaults={
#                           'first_name': first_name.strip(),
#                           'last_name': last_name.strip(),
#                           'email': ''
#                         }
#                     )
#                     student, student_created = Student.objects.get_or_create(
#                         first_name=first_name.strip(),
#                         last_name=last_name.strip(),
#                         user=user,
#                     )
#                     if user_created:
#                         created_count += 1
#                     if not student_created:
#                         updated_count += 1
#
#                   except Exception as e:
#                       errors.append(f"Row {row_num} ('{first_name} {last_name}'): Error - {str(e)}")
#
#               if errors:
#                   for error_msg in errors:
#                     self.message_user(request, error_msg, level='WARNING')
#
#               success_msg_parts = []
#               if created_count > 0:
#                 success_msg_parts.append(f"{created_count} new students were created")
#               if updated_count > 0 and created_count == 0:
#                 success_msg_parts.append(f"{updated_count} students were updated (already existed)")
#               elif updated_count > 0:
#                 success_msg_parts.append(f"and {updated_count} existing student(s) processed")
#
#               if success_msg_parts:
#                   self.message_user(request, f"{' '.join(success_msg_parts)} successfully.", level='SUCCESS')
#
#               elif not errors:  # No new, no updates, no errors
#                   self.message_user(request, "CSV processed. No new students were added (they may already exist or CSV was empty).", level='INFO')
#
#           except Exception as e:
#               self.message_user(request, f"Error processing CSV file: {str(e)}", level='ERROR')
#
#           return redirect(request.path)
#
#     # End the if statement
#     else:
#         from .forms import CSVUploadForm
#         form = CSVUploadForm()
#     context = {
#         'form': form,
#         'opts': self.model._meta,
#         'app_label': self.model._meta.app_label,
#     }
#     return render(request, 'admin/upload_csv.html', context)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)