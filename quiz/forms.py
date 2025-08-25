from django import forms
from django.contrib.auth.models import User
from . import models

class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

class CourseForm(forms.ModelForm):
    class Meta:
        model=models.Course
        fields=['course_name','question_number','total_marks']

class QuestionForm(forms.ModelForm):
    # This will show dropdown __str__ method course model is shown on html so override it
    # to_field_name this will fetch corresponding value user_id present in course model and return it
    courseID=forms.ModelChoiceField(queryset=models.Course.objects.all(),empty_label="Course Name", to_field_name="id")
    
    class Meta:
        model=models.Question
        fields=['marks','question','option1','option2','option3','option4','answer','excel_file']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
        }
    
    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['excel_file'].help_text = 'Upload an Excel file with questions. Format: question, option1, option2, option3, option4, answer, marks'
        self.fields['excel_file'].required = False

# Add a new form for bulk Excel upload
class BulkQuestionForm(forms.Form):
    course = forms.ModelChoiceField(queryset=models.Course.objects.all(), empty_label="Select Course")
    excel_file = forms.FileField(label='Excel File')
    
    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if excel_file:
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError("Only Excel files are allowed.")
        return excel_file