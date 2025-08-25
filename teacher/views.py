from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from student import models as SMODEL
from quiz import forms as QFORM
import pandas as pd
from django.core.exceptions import ValidationError



#for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'teacher/teacherclick.html')

def teacher_signup_view(request):
    userForm=forms.TeacherUserForm()
    teacherForm=forms.TeacherForm()
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=forms.TeacherUserForm(request.POST)
        teacherForm=forms.TeacherForm(request.POST,request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacher=teacherForm.save(commit=False)
            teacher.user=user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect('teacherlogin')
    return render(request,'teacher/teachersignup.html',context=mydict)



def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    'total_student':SMODEL.Student.objects.all().count()
    }
    return render(request,'teacher/teacher_dashboard.html',context=dict)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request,'teacher/teacher_exam.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm=QFORM.CourseForm()
    if request.method=='POST':
        courseForm=QFORM.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-exam')
    return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/teacher/teacher-view-exam')

@login_required(login_url='teacherlogin')
def teacher_question_view(request):
    return render(request,'teacher/teacher_question.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    from quiz.models import Question, Course
    questionForm = QFORM.QuestionForm()
    bulkForm = forms.BulkQuestionForm()

    if request.method == 'POST':
        if 'excel_file' in request.FILES:  # Bulk Excel upload
            bulkForm = forms.BulkQuestionForm(request.POST, request.FILES)
            if bulkForm.is_valid():
                course = bulkForm.cleaned_data['course']
                excel_file = bulkForm.cleaned_data['excel_file']

                import pandas as pd
                from django.core.exceptions import ValidationError

                try:
                    df = pd.read_excel(excel_file)
                    required_columns = ['question', 'option1', 'option2', 'option3', 'option4', 'answer', 'marks']
                    for col in required_columns:
                        if col not in df.columns:
                            raise ValidationError(f"Missing column in Excel: {col}")

                    for _, row in df.iterrows():
                        Question.objects.create(
                            course=course,
                            question=row['question'],
                            option1=row['option1'],
                            option2=row['option2'],
                            option3=row.get('option3', ''),
                            option4=row.get('option4', ''),
                            answer=row['answer'],
                            marks=row['marks']
                        )

                    return HttpResponseRedirect('/teacher/teacher-view-question')

                except Exception as e:
                    bulkForm.add_error('excel_file', f"Error processing file: {str(e)}")

        else:  # Single question form
            questionForm = QFORM.QuestionForm(request.POST)
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                question.save()
                return HttpResponseRedirect('/teacher/teacher-view-question')

    return render(request, 'teacher/teacher_add_question.html', {
        'questionForm': questionForm,
        'bulkForm': bulkForm
    })

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses= QMODEL.Course.objects.all()
    return render(request,'teacher/teacher_view_question.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request,pk):
    questions=QMODEL.Question.objects.all().filter(course_id=pk)
    return render(request,'teacher/see_question.html',{'questions':questions})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request,pk):
    question=QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')
