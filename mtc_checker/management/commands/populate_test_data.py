import random
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from mtc_checker.models import Student, TestAttempt
from mtc_checker.question_generator import MTCQuestionGenerator
from django.contrib.auth.models import User # Added for user management
import string #Added to be able to work with the strings
from faker import Faker  # Import Faker

NUM_STUDENTS = 60
NUM_TESTS_PER_STUDENT = 40
MAX_SCORE = 25
MIN_SCORE_START = 5
IMPROVEMENT_RATE = 0.5
PERFECT_SCORE_CHANCE_OVERALL = 0.1
PERFECT_SCORE_CHANCE_IMPROVING_LATER = 0.3

FIRST_NAMES = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Harry", "Ivy", "Jack",
               "Katie", "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Ryan", "Sophia", "Tom",
               "Uma", "Victor", "Wendy", "Xander", "Yara", "Zack", "Ava", "Ben", "Chloe", "Daniel",
               "Ella", "Finn", "Gia", "Henry", "Isla", "Jake", "Lily", "Mason", "Nora", "Owen",
               "Penelope", "Quentin", "Ruby", "Samuel", "Thea", "Ulysses", "Violet", "William", "Xenia",
               "Yasmine", "Adrian", "Beatrice", "Caspian", "Daphne", "Ezra", "Felicity"]
LAST_NAMES = ["Smith", "Jones", "Brown", "Davis", "Wilson", "Garcia", "Rodriguez", "Williams", "Johnson", "Lee",
              "Walker", "Perez", "Hall", "Young", "Allen", "King", "Wright", "Lopez", "Hill", "Green",
              "Baker", "Nelson", "Carter", "Mitchell", "Roberts", "Gomez", "Jackson", "Lewis", "Clark", "White",
              "Adams", "Barnes", "Gray", "Cook", "Price", "Bennett", "Wood", "Ross", "Collins", "Bell",
              "Murphy", "Rivera", "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres", "Peterson", "Gray"]

class Command(BaseCommand):
    help = 'Populates dummy test attempt data for specified students.'

    def handle(self, *args, **options):
        self.stdout.write("Starting to populate test data...")

        #Delete old Students
        TestAttempt.objects.all().delete()
        Student.objects.all().delete()
        User.objects.all().exclude(is_superuser=True).delete() # Also deletes the created User Object

        self.stdout.write(self.style.WARNING("Deleted all existing test attempts and students."))

        faker = Faker()
        students_to_process = []

        # Create Students
        for i in range(NUM_STUDENTS):
            # Generate fake username and name
            username = f"student{i+1}"
            password = self.generate_random_password()  # Default length 10
            email = faker.email()  # Generate a fake email.  You might also do f"{username}@example.com"

            # create the user
            user = User.objects.create_user(username=username, password=password,
                                           email=email, first_name=faker.first_name(),
                                           last_name=faker.last_name())

            first_name = faker.first_name()
            last_name = faker.last_name()

            student = Student.objects.create(first_name=first_name, last_name=last_name, user=user)
            students_to_process.append(student)
           
            self.stdout.write(f"Created student: {first_name} {last_name} with username:{username}  ")

        num_students = len(students_to_process)
        num_improving_students = int(num_students * IMPROVEMENT_RATE)

        random.shuffle(students_to_process)
        improving_students_set = set(students_to_process[:num_improving_students])

        generator = MTCQuestionGenerator()  # Instantiate your question generator

        all_possible_questions = []
        for i in range(2, 13):
            for j in range(2, 13):
                all_possible_questions.append({'op1': i, 'op2': j, 'answer': i * j})

        for student in students_to_process:
            self.stdout.write(f"Processing student: {student.first_name} {student.last_name}")
            is_improving_student = student in improving_students_set
            current_max_possible_score = 5 if is_improving_student else 15

            for i in range(NUM_TESTS_PER_STUDENT):
                timestamp_offset = sum(random.randint(1, 3) for _ in range(i + 1))
                test_timestamp = datetime.now() - timedelta(days=(NUM_TESTS_PER_STUDENT * 3) - timestamp_offset + random.randint(0, 2))

                questions_for_this_test = generator.generate_test_questions()
                answered_questions = []  # Clear the answer for this time

                correct_answers_count = 0
                for question in questions_for_this_test:
                    # Determine if the answer is correct based on the student type and test number
                    is_correct = False
                    if is_improving_student:
                        if random.random() < (0.3 + (i / NUM_TESTS_PER_STUDENT) * 0.4):
                            is_correct = True
                    else:
                        is_correct = random.random() < 0.5

                    if is_correct:
                        correct_answers_count += 1

                    answered_questions.append({
                        'op1': question['op1'],
                        'op2': question['op2'],
                        'correct': int(is_correct)
                    })
                score = correct_answers_count

                # Ensure score is within bounds
                score = max(0, min(score, MAX_SCORE))

                TestAttempt.objects.create(
                    student=student,
                    score=score,
                    total_questions=MAX_SCORE,
                    timestamp=test_timestamp,
                    test_data={
                        'source': 'dummy_data_generator',
                        'attempt_num': i + 1,
                        'answered_questions': answered_questions  # Store which questions the student actually answered
                    }
                )
            self.stdout.write(self.style.SUCCESS(f"Generated {NUM_TESTS_PER_STUDENT} tests for {student.first_name} {student.last_name}."))

        self.stdout.write(self.style.SUCCESS("Successfully populated dummy test data."))

    def generate_random_password(self, length=10):
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for i in range(length))
        return password