from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
import pandas as pd
from django.core.exceptions import ValidationError


def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request, 'quiz/index.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()


def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
    elif is_teacher(request.user):
        accountapproval = TMODEL.Teacher.objects.all().filter(user_id=request.user.id, status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')
        else:
            return render(request, 'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')


def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


# ---------------- ADMIN DASHBOARD ---------------- #

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict = {
        'total_student': SMODEL.Student.objects.all().count(),
        'total_teacher': TMODEL.Teacher.objects.all().filter(status=True).count(),
        'total_course': models.Course.objects.all().count(),
        'total_question': models.Question.objects.all().count(),
    }
    return render(request, 'quiz/admin_dashboard.html', context=dict)


@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict = {
        'total_teacher': TMODEL.Teacher.objects.all().filter(status=True).count(),
        'pending_teacher': TMODEL.Teacher.objects.all().filter(status=False).count(),
        'salary': TMODEL.Teacher.objects.all().filter(status=True).aggregate(Sum('salary'))['salary__sum'],
    }
    return render(request, 'quiz/admin_teacher.html', context=dict)


@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=True)
    return render(request, 'quiz/admin_view_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
def update_teacher_view(request, pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    user = TMODEL.User.objects.get(id=teacher.user_id)
    userForm = TFORM.TeacherUserForm(instance=user)
    teacherForm = TFORM.TeacherForm(request.FILES, instance=teacher)
    mydict = {'userForm': userForm, 'teacherForm': teacherForm}
    if request.method == 'POST':
        userForm = TFORM.TeacherUserForm(request.POST, instance=user)
        teacherForm = TFORM.TeacherForm(request.POST, request.FILES, instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request, 'quiz/update_teacher.html', context=mydict)


@login_required(login_url='adminlogin')
def delete_teacher_view(request, pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    user = User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')


@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=False)
    return render(request, 'quiz/admin_view_pending_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
def approve_teacher_view(request, pk):
    teacherSalary = forms.TeacherSalaryForm()
    if request.method == 'POST':
        teacherSalary = forms.TeacherSalaryForm(request.POST)
        if teacherSalary.is_valid():
            teacher = TMODEL.Teacher.objects.get(id=pk)
            teacher.salary = teacherSalary.cleaned_data['salary']
            teacher.status = True
            teacher.save()
        return HttpResponseRedirect('/admin-view-pending-teacher')
    return render(request, 'quiz/salary_form.html', {'teacherSalary': teacherSalary})


@login_required(login_url='adminlogin')
def reject_teacher_view(request, pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    user = User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-pending-teacher')


@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers = TMODEL.Teacher.objects.all().filter(status=True)
    return render(request, 'quiz/admin_view_teacher_salary.html', {'teachers': teachers})


# ---------------- STUDENTS ---------------- #

@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict = {
        'total_student': SMODEL.Student.objects.all().count(),
    }
    return render(request, 'quiz/admin_student.html', context=dict)


@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students = SMODEL.Student.objects.all()
    return render(request, 'quiz/admin_view_student.html', {'students': students})


@login_required(login_url='adminlogin')
def update_student_view(request, pk):
    student = SMODEL.Student.objects.get(id=pk)
    user = User.objects.get(id=student.user_id)

    userForm = SFORM.StudentUserForm(instance=user)
    studentForm = SFORM.StudentForm(instance=student)

    if request.method == 'POST':
        userForm = SFORM.StudentUserForm(request.POST, instance=user)
        studentForm = SFORM.StudentForm(request.POST, request.FILES, instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')

    context = {'userForm': userForm, 'studentForm': studentForm}
    return render(request, 'quiz/update_student.html', context)
@login_required(login_url='adminlogin')
def delete_student_view(request, pk):
    student = SMODEL.Student.objects.get(id=pk)
    user = User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


# ---------------- STUDENT EXAM ---------------- #

@login_required
def calculate_marks(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        course = models.Course.objects.get(id=course_id)
        questions = models.Question.objects.filter(course=course)

        total_marks = 0
        obtained_marks = 0

        for q in questions:
            # assume form field names are "question_<id>"
            selected_answer = request.POST.get(f'question_{q.id}')
            if selected_answer == q.answer:
                obtained_marks += q.marks
            total_marks += q.marks

        # save result
        student = SMODEL.Student.objects.get(user=request.user)
        models.Result.objects.create(
            student=student,
            exam=course,
            marks=obtained_marks
        )

        return render(request, 'student/view_result.html', {
            'course': course,
            'obtained_marks': obtained_marks,
            'total_marks': total_marks
        })

    return redirect('student-dashboard')

# ---------------- COURSES ---------------- #

@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request, 'quiz/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm = forms.CourseForm()
    if request.method == 'POST':
        courseForm = forms.CourseForm(request.POST)
        if courseForm.is_valid():
            courseForm.save()
        return HttpResponseRedirect('/admin-view-course')
    return render(request, 'quiz/admin_add_course.html', {'courseForm': courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request, 'quiz/admin_view_course.html', {'courses': courses})


@login_required(login_url='adminlogin')
def delete_course_view(request, pk):
    course = models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')


# ---------------- QUESTIONS ---------------- #

@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request, 'quiz/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm = forms.QuestionForm()
    bulkForm = forms.BulkQuestionForm()

    if request.method == 'POST':
        if 'excel_file' in request.FILES:   # Bulk Excel upload
            bulkForm = forms.BulkQuestionForm(request.POST, request.FILES)
            if bulkForm.is_valid():
                course = bulkForm.cleaned_data['course']
                excel_file = bulkForm.cleaned_data['excel_file']

                try:
                    df = pd.read_excel(excel_file)
                    required_columns = ['question', 'option1', 'option2', 'option3', 'option4', 'answer', 'marks']
                    for col in required_columns:
                        if col not in df.columns:
                            raise ValidationError(f"Missing column in Excel: {col}")

                    for _, row in df.iterrows():
                        models.Question.objects.create(
                            course=course,
                            marks=row['marks'],
                            question=row['question'],
                            option1=row['option1'],
                            option2=row['option2'],
                            option3=row.get('option3', ''),
                            option4=row.get('option4', ''),
                            answer=row['answer']
                        )

                    return HttpResponseRedirect('/admin-view-question')

                except Exception as e:
                    bulkForm.add_error('excel_file', f"Error processing file: {str(e)}")

        else:   # Single question form
            questionForm = forms.QuestionForm(request.POST)
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                course = models.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                question.save()
                return HttpResponseRedirect('/admin-view-question')

    return render(request, 'quiz/admin_add_question.html', {
        'questionForm': questionForm,
        'bulkForm': bulkForm
    })


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses = models.Course.objects.all()
    return render(request, 'quiz/admin_view_question.html', {'courses': courses})


@login_required(login_url='adminlogin')
def view_question_view(request, pk):
    questions = models.Question.objects.all().filter(course_id=pk)
    return render(request, 'quiz/view_question.html', {'questions': questions})


@login_required(login_url='adminlogin')
def delete_question_view(request, pk):
    question = models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')


# ---------------- MARKS ---------------- #

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students = SMODEL.Student.objects.all()
    return render(request, 'quiz/admin_view_student_marks.html', {'students': students})


@login_required(login_url='adminlogin')
def admin_view_marks_view(request, pk):
    courses = models.Course.objects.all()
    response = render(request, 'quiz/admin_view_marks.html', {'courses': courses})
    response.set_cookie('student_id', str(pk))
    return response


@login_required(login_url='adminlogin')
def admin_check_marks_view(request, pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student = SMODEL.Student.objects.get(id=student_id)
    results = models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request, 'quiz/admin_check_marks.html', {'results': results})


# ---------------- STATIC PAGES ---------------- #

def aboutus_view(request):
    return render(request, 'quiz/aboutus.html')


def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name = sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently=False)
            return render(request, 'quiz/contactussuccess.html')
    return render(request, 'quiz/contactus.html', {'form': sub})
