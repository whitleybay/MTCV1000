from django.contrib.auth.models import User
from django.db import models
import uuid
from django.core.validators import MaxValueValidator, MinValueValidator

class Student(models.Model):
    student_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    email = models.EmailField(blank=True, null=True)  # ADDED LINE - IS THIS IN THE FILE?

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class TestAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attempts')
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(25)])
    total_questions = models.IntegerField(default=25)
    timestamp = models.DateTimeField(auto_now_add=True)
    test_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - Score: {self.score}"