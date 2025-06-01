from django import forms
from .models import Student
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class StudentLoginForm(AuthenticationForm):
    pass # We only care about Username and Password for this case
    # You could add additional validation or fields here if needed

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'user'] # Include the User field
        # Customize widgets if needed (e.g., for a select field for the User)


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File")

class StudentCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, help_text="Student's First Name")
    last_name = forms.CharField(max_length=100, required=True, help_text="Student's Last Name")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            student = Student.objects.create(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                user=user  # link the newly created Student to the User
            )
            student.save()

        return user