from django.db import models
import os
import pandas as pd
from django.core.exceptions import ValidationError


# File upload path
def question_file_path(instance, filename):
    return os.path.join('questions', 'excel', filename)


class Course(models.Model):
    course_name = models.CharField(max_length=50)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()

    def __str__(self):
        return self.course_name


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField(blank=True, null=True)
    question = models.CharField(max_length=600, blank=True, null=True)
    option1 = models.CharField(max_length=200, blank=True, null=True)
    option2 = models.CharField(max_length=200, blank=True, null=True)
    option3 = models.CharField(max_length=200, blank=True, null=True)
    option4 = models.CharField(max_length=200, blank=True, null=True)

    cat = (
        ('Option1', 'Option1'),
        ('Option2', 'Option2'),
        ('Option3', 'Option3'),
        ('Option4', 'Option4'),
    )
    answer = models.CharField(max_length=200, choices=cat, blank=True, null=True)

    # Field for Excel upload
    excel_file = models.FileField(upload_to=question_file_path, blank=True, null=True)

    def clean(self):
        """
        Validate that either individual fields OR Excel file is provided, not both.
        """
        if self.excel_file and (self.question or self.option1 or self.option2 or self.option3 or self.option4):
            raise ValidationError("Provide either an Excel file OR individual question data, not both.")

    def save(self, *args, **kwargs):
        """
        If Excel uploaded → parse and bulk create Questions.
        If manual entry → save as usual.
        """
        if self.excel_file:
            file_path = self.excel_file.path
            try:
                df = pd.read_excel(file_path)

                for _, row in df.iterrows():
                    Question.objects.create(
                        course=self.course,
                        marks=row.get('marks', 1),
                        question=row['question'],
                        option1=row['option1'],
                        option2=row['option2'],
                        option3=row.get('option3', ''),
                        option4=row.get('option4', ''),
                        answer=row['answer'],
                    )

                # Remove the uploaded Excel file after processing
                os.remove(file_path)

                # Don’t save the dummy row itself → just return
                return

            except Exception as e:
                raise ValidationError(f"Error processing Excel file: {str(e)}")

        # Normal manual question save
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question if self.question else f"Excel Upload for {self.course}"


class Result(models.Model):
    student = models.ForeignKey('student.Student', on_delete=models.CASCADE)
    exam = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.exam} ({self.marks} marks)"
