from django import forms
from django.contrib.auth.models import User
from . import models

class TeacherUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }

class TeacherForm(forms.ModelForm):
    class Meta:
        model=models.Teacher
        fields=['address','mobile','profile_pic']

class BulkQuestionForm(forms.Form):
    course = forms.ModelChoiceField(queryset=None)
    excel_file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(BulkQuestionForm, self).__init__(*args, **kwargs)
        from quiz.models import Course
        self.fields['course'].queryset = Course.objects.all()


