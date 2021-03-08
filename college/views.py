from django.core.mail import send_mail
from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect, reverse
from django.template.loader import get_template
from django.utils.encoding import force_bytes
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required

import secrets, random
import string
import datetime

year_s = datetime.datetime.today().year
YEARS = list(range(year_s, year_s - 6, -1))


# user forgot password
def userForgotPassword(request):
    if request.POST:
        email = request.POST.get('email')

        user = Account.object.get(email=email)
        to_email = [user.email, ]

        token_generator = default_token_generator
        use_https = False
        extra_email_context = None
        subject_template_name = "password_reset_subject.txt"
        email_template_name = "password_reset_email.html"
        from_email = "admin@gmail.com"
        user = Account.object.get(email=email)
        domain = request.get_host()

        context = {
            'email': to_email,
            'domain': domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        from django.template import loader
        subject = loader.render_to_string(subject_template_name, context)

        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        send_mail(
            subject,
            body,
            from_email,
            [to_email],
            fail_silently=False,
        )
        return redirect("college:reset_done")

    return render(request=request, template_name="forgot_password.html", )


def resetDone(request):
    return render(request=request, template_name="password_reset_done.html")


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.exceptions import ValidationError

INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


def reset(request, uidb64, token):
    validlink = False

    if request.POST:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.object.get(id=uid)
        password = request.POST.get('password_confirm')
        user.set_password(password)
        user.save()
        return HttpResponseRedirect(reverse("college:reset_done"))


    else:
        token_generator = default_token_generator
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()

            user = Account.object.get(pk=uid)
            if user is not None:
                if token_generator.check_token(user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    form = {}
                    validlink = True
            else:
                return render(request, "student/404.html")

        except (Account.DoesNotExist, ValidationError):
            return render(request, "student/404.html")
    return render(request, "password_reset_confirm.html",
                  context={'validlink': validlink, })


#


# initializing size of string

def gen():
    N = 7
    res = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(N))
    res = 'PCMT' + str(datetime.datetime.today().year) + res
    return res


def index(request):
    return render(request, "homepage.html")


@login_required(login_url='college:login')
def home_staff(request):
    return render(request, "home_staff.html")


@login_required(login_url='college:login')
def home_student(request):
    return render(request, "home_student.html")


def home_general(request):
    return render(request, "home_general.html")


def sidebar(request):
    return render(request, "base.html")


def course(request):
    return render(request, "course.html")


def about(request):
    return render(request, "about.html")


from django.contrib.auth import authenticate, login as auth_login, logout


def signup(request):
    if request.POST:
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        if password != password_confirm:
            msg = "password does not match"
            color = 'danger'
            return render(request, "signup.html", context={'msg': msg, 'color': color})

        else:
            if len(password) >= 8:
                if password.isdigit():
                    msg = "password should atleaset 8 charactor and combination with alphanumberic charactor"
                    color = 'danger'
                    return render(request, "signup.html", context={'msg': msg, 'color': color})

                else:
                    if password.isalpha():
                        msg = "password should atleaset 8 charactor and combination with alphanumberic charactor"
                        color = 'danger'
                        return render(request, "signup.html", context={'msg': msg, 'color': color})
                    else:

                        try:
                            user = Account.object.create_user(email=request.POST.get('email'),
                                                              password=request.POST.get('password'))
                            user.enrollment_no = gen()
                            user.is_student = True
                            user.save()
                            msg = 'successfully submitted Try to login'
                            color = 'success'
                            return render(request, "signup.html", context={'msg': msg, 'color': color})
                        except IntegrityError:
                            msg = 'Email already Exist'
                            color = 'danger'
                            return render(request, "signup.html", context={'msg': msg, 'color': color})
            else:

                msg = "password should atleaset 8 charactor and combination with alphanumberic charactor"
                color = 'danger'
                return render(request, "signup.html", context={'msg': msg, 'color': color})
    return render(request, 'signup.html')


from .models import Staff, ExamData


def login(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect("college:home_student")
        elif request.user.is_teacher:
            return redirect("college:home_staff")
        else:
            return redirect('college:student_data_view')
    elif request.POST:
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(email=email, password=password)
        if user:
            auth_login(request, user)
            if request.user.is_teacher:
                usr = Staff.object.get(email=email)
                request.session['email'] = email
                request.session['department'] = usr.department
                request.session['image'] = usr.image.url
                request.session['active'] = usr.active
                request.session['first_name'] = usr.first_name
                request.session['last_name'] = usr.last_name
            if request.user.is_staff and not request.user.is_admin:
                usr = Staff.object.get(email=email)
                request.session['email'] = email
                request.session['department'] = usr.department
                request.session['image'] = usr.image.url
                request.session['active'] = usr.active
                request.session['first_name'] = usr.first_name
                request.session['last_name'] = usr.last_name
                return redirect('college:admission_data')
            elif request.user.is_teacher:
                usr = Staff.object.get(email=email)
                request.session['email'] = email
                request.session['department'] = usr.department
                request.session['image'] = usr.image.url
                request.session['active'] = usr.active
                request.session['first_name'] = usr.first_name
                request.session['last_name'] = usr.last_name
                return redirect('college:home_staff')
            elif request.user.is_student:
                usr = Student.objects.get(email=email)
                request.session['email'] = email
                request.session['department'] = usr.department
                request.session['image'] = usr.photo.url
                request.session['first_name'] = usr.first_name
                request.session['last_name'] = usr.last_name
                return redirect('college:home_student')
            else:
                return redirect('college:student_data_view')
        else:
            msg = 'Email or Password is not match'
            color = 'danger'
            return render(request, "login.html", context={'msg': msg, 'color': color})

    return render(request, "login.html")


def forgot_password(request):
    return render(request, "forgot_password.html")


def log_out(request):
    logout(request)
    return redirect("college:login")


from .models import Account


def profile(request, id):
    user = Student.objects.get(id=id)
    if request.POST:
        return HttpResponse("<h1> greate </h1>")
    return render(request, "profile.html", {'users': user})


def contact(request):
    if request.POST:
        return HttpResponse("<h1> greate </h1>")
    return render(request, "contact.html")


# pdf creator

def render_to_pdf(template_path, context_dict={}, name=''):
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = ' filename="' + name + '.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context_dict)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response, )
    # if error then show some funy view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def download_report(request):
    if request.user.is_student:
        semester = request.POST.get('semester')
        subjects = Subject.objects.filter(semester=semester, department=request.session['department'])
        user = Account.object.get(is_student=True, id=request.user.id)
        student_obj = Student.objects.get(email=user.email)

        result = Result.objects.filter(semester=semester, student_id=student_obj.id)

        template_path = 'download_report.html'

        context = {'user': user, 'subjects': subjects, 'result': result, 'semester': semester, 'exam': exam,
                   'student_obj': student_obj}
        response = render_to_pdf(template_path, context, name=(request.session['department'] + " student Database"))

    elif request.user.is_teacher:

        subject_id = request.POST.get('subject_id')
        semester = request.POST.get('semester')

        subjects = Subject.objects.get(id =subject_id)

        user = Account.object.get(is_teacher=True, id=request.user.id)
        staff = Staff.object.get(email=user.email)

        result = Result.objects.filter(semester=semester, department=staff.department,subject_id=subject_id)

        template_path = 'download_report.html'

        context = {'user': user, 'subjects': subjects, 'result': result, 'semester': semester,}
        response = render_to_pdf(template_path, context, name=(request.session['department'] + " student Database"))
    return response


def view_reports(request):
    if request.POST:
        if request.user.is_student:
            student_obj = Student.objects.get(email=request.session['email'])
            current_semester = student_obj.semester
            semester = int(request.POST.get('semester'))

            return render(request, 'view_reports.html', {'semester': semester, 'current_semester': current_semester})
        elif request.user.is_teacher:
            staff_obj = Staff.object.get(email=request.session['email'])
            subjects = Subject.objects.filter(teacher_id = staff_obj.id,allocated=True)
            semester = int(request.POST.get('semester'))

            return render(request, 'view_reports.html', {'semester': semester,'subjects':subjects,'staff_obj':staff_obj})

    return render(request, 'view_reports.html', {'semester': request.POST.get('semester'), 'current_semester': {}})


def export_student_data_pdf(request):
    if request.user.is_authenticated:
        if request.user.is_HOD:
            user = Account.object.filter(is_student=True, department=request.user.department)
            template_path = 'export_student_data_pdf.html'
            context = {'users': user, 'hod': True, 'department': request.user.department}
            response = render_to_pdf(template_path, context, name=(request.user.department + " student Database"))
            return response
        elif request.user.is_BOC:
            user = Account.object.filter(is_student=True, department=request.user.department, year=request.user.year,
                                         semester=1)
            template_path = 'export_student_data_pdf.html'
            context = {'users': user, 'boc': True, 'year': request.user.year}
            response = render_to_pdf(template_path, context, name=(request.user.department + " student Database"))
            return response
        elif request.user.is_admin:
            user = Account.object.filter(is_student=True, )
            template_path = 'export_student_data_pdf.html'
            context = {'users': user, 'admin': True}
            response = render_to_pdf(template_path, context, name=(request.user.department + " student Database"))
            return response


def export_pdf(request, email):
    user = Student.objects.get(email=email)

    template_path = 'export_pdf.html'
    context = {'user': user}

    response = render_to_pdf(template_path, context, name=(user.first_name + user.last_name))
    return response

    return render(request, 'pdf_output.html', {'users': user})


from .models import Question, Subject


def exam(request):
    if request.POST:
        if request.user.is_student:
            user = Student.objects.get(email=request.user.email)
            if request.POST.get('semester') is not None:
                if user.semester == int(request.POST.get('semester')):
                    exam_details = ExamData.objects.filter(department=request.session['department'],
                                                           semester=request.POST.get('semester'), )

                    return render(request, 'exam.html',
                                  {'exam_details': exam_details, })
        elif request.user.is_teacher:

            staff = Staff.object.get(email=request.user.email)

            exam_details = ExamData.objects.filter(department=request.session['department'],
                                                   semester=request.POST.get('semester'), teacher_id=staff.id)

            return render(request, 'exam.html',
                          {'exam_details': exam_details, })

        elif request.user.is_admin:
            subjects = Subject.objects.filter(department=request.session['department'],
                                              semester=request.POST.get('semester'))
            exam_details = ExamData.objects.filter(department=request.session['department'],
                                                   semester=request.POST.get('semester'), )

            return render(request, 'exam.html',
                          {'exam_details': exam_details, })

    subjects = {}
    total_question = {}
    return render(request, 'exam.html', {'subjects': subjects, 'total_question': total_question})


# for student
from .models import Result, Subject


def marks_add_database(semester, ca, subject, option, correct_ans, email):
    get_subject = Subject.objects.get(id=subject)
    student = Student.objects.get(email=email)
    obj = ExamData.objects.get(exam=ca, subject_id=subject, semester=semester)
    try:
        result_obj = Result.objects.get(semester=semester, exam=ca, subject=get_subject.id,
                                        student=student.id)
        if int(ca) == 1:
            if int(option) == correct_ans.correct and (result_obj.ca1_marks < obj.total_marks):
                result_obj.ca1_marks = result_obj.ca1_marks + 1
        elif int(ca) == 2:
            if int(option) == correct_ans.correct and (result_obj.ca2_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca2_marks + 1
        elif int(ca) == 3:
            if int(option) == correct_ans.correct and (result_obj.ca3_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca3_marks + 1
        elif int(ca) == 4:
            if int(option) == correct_ans.correct and (result_obj.ca4_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca4_marks + 1
        result_obj.save()

    except:
        result_obj = Result()
        result_obj.student = student
        result_obj.subject = get_subject
        result_obj.semester = semester
        result_obj.total_marks = obj
        result_obj.exam = ca
        result_obj.exam_done = False
        result_obj.department = student.department

        if int(ca) == 1:
            if int(option) == correct_ans.correct and (result_obj.ca1_marks < obj.total_marks):
                result_obj.ca1_marks = result_obj.ca1_marks + 1
        elif int(ca) == 2:
            if int(option) == correct_ans.correct and (result_obj.ca2_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca2_marks + 1
        elif int(ca) == 3:
            if int(option) == correct_ans.correct and (result_obj.ca3_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca3_marks + 1
        elif int(ca) == 4:
            if int(option) == correct_ans.correct and (result_obj.ca4_marks < obj.total_marks):
                result_obj.ca2_marks = result_obj.ca4_marks + 1
        result_obj.save()


def message(sms):
    msg1 = '''<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
                        <div class="jumbotron jumbotron-fluid">
                         <div class="container">
                           <h1 class="display-4">
                           '''

    msg2 = '''
                           </h1>
                           <p class="lead">.</p>
                           <p class="lead">
                           <a class="btn btn-primary btn-lg" href="../../../../exam" role="button">Back Home</a>
                         </p>
                         </div>
                       </div>
                           '''
    return msg1 + sms + msg2


def question_view(request, semester, ca, subject, question_id):
    if request.POST:
        percentage = request.POST.get('percentage')
        # count_value = float(request.POST.get('count_value'))
        count_value = 0
        get_subject = Subject.objects.get(id=subject)

        obj = ExamData.objects.get(exam=ca, subject_id=subject, semester=semester)
        if obj.allow_test:

            student = Student.objects.get(email=request.user.email)
            correct_ans = Question.objects.get(semester=semester, exam=ca, subject=get_subject.id,
                                               question_no=question_id)
            print(request.POST.get('option'))
            if question_id == 1 and (request.POST.get('option') != None):
                option = request.POST.get('option')
                # exam
                marks_add_database(semester=semester, ca=ca, option=option, correct_ans=correct_ans,
                                   email=student.email, subject=subject)
                question_id += 1

                if question_id <= obj.total_question:
                    que = Question.objects.get(semester=semester, exam=ca, question_no=question_id, subject=subject)
                    return render(request, 'question_view.html',
                                  {'que': que, 'count_value': count_value,
                                   'percentage': percentage,
                                   'semester': semester,
                                   'ca': ca,
                                   'subject': get_subject.id,
                                   'question_id': question_id,
                                   'total_question': obj.total_question + 1})
                else:
                    result_obj = Result.objects.get(semester=semester, exam=ca, subject=get_subject.id,
                                                    student=student.id)
                    result_obj.exam_done = True
                    result_obj.save()
                    return HttpResponse(message('Exam finish'))


            elif request.POST.get('option') != None:
                option = request.POST.get('option')
                # exam
                marks_add_database(semester=semester, ca=ca, option=option, correct_ans=correct_ans,
                                   email=student.email, subject=subject)

                question_id += 1
                if question_id <= obj.total_question:
                    que = Question.objects.get(semester=semester, exam=ca, question_no=question_id, subject=subject)
                    return render(request, 'question_view.html',
                                  {'que': que, 'count_value': count_value,
                                   'percentage': percentage,
                                   'semester': semester,
                                   'ca': ca,
                                   'subject': get_subject.id,
                                   'question_id': question_id,
                                   'total_question': obj.total_question + 1})
                else:
                    result_obj = Result.objects.get(semester=semester, exam=ca, subject=get_subject.id,
                                                    student=student.id)
                    result_obj.exam_done = True
                    result_obj.save()
                    return HttpResponse(message('Exam finish'))
            else:
                msg = 'Please select any of the option'
                color = 'danger'
                que = Question.objects.get(semester=semester, exam=ca, question_no=question_id, subject=subject)
                return render(request, 'question_view.html',
                              {'que': que, 'count_value': count_value,
                               'percentage': percentage,
                               'semester': semester,
                               'ca': ca,
                               'subject': get_subject.id,
                               'question_id': question_id,
                               'total_question': obj.total_question + 1,
                               'msg': msg,
                               'color': color})

        else:
            return HttpResponse(message('Exam is not stated yet'))

    count_value = 0
    percentage = 0
    get_subject = Subject.objects.get(id=subject)
    student = Student.objects.get(email=request.user.email)
    try:
        obj = Result.objects.get(semester=semester, exam=ca, subject=get_subject.id, student=student.id)
        if obj.exam_done:
            return HttpResponse(message('Exam is over Try Next Time'))
        else:
            obj = ExamData.objects.get(exam=ca, subject_id=subject, semester=semester)
            if obj.allow_test:
                que = Question.objects.get(semester=semester, exam=ca, question_no=question_id, subject=subject)
                return render(request, 'question_view.html',
                              {'que': que, 'count_value': count_value,
                               'percentage': percentage,
                               'semester': semester,
                               'ca': ca,
                               'subject': get_subject.id,
                               'question_id': question_id})
            else:
                return HttpResponse(message('Exam is not Started yet try few minutes later'))

    except:
        try:
            obj = ExamData.objects.get(exam=ca, subject_id=subject, semester=semester)
            if obj.allow_test:
                que = Question.objects.get(semester=semester, exam=ca, question_no=question_id, subject=subject)

                return render(request, 'question_view.html',
                              {'que': que, 'count_value': count_value,
                               'percentage': percentage,
                               'semester': semester,
                               'ca': ca,
                               'subject': get_subject.id,
                               'question_id': question_id,
                               'total_question': obj.total_question + 1
                               })
            else:
                return HttpResponse(message('Exam is not Started yet try few minutes later'))
        except:
            return HttpResponse(message('Exam is not conducted yet'))


# for teacher
def question(request, semester, ca, subject):
    subject = Subject.objects.get(id=subject)
    questions = Question.objects.filter(semester=semester, exam=ca, subject=subject)
    if request.POST:
        if request.POST.get('allow'):
            examDataObj = ExamData.objects.get(semester=semester, exam=ca, subject_id=subject)
            examDataObj.allow_test = True
            examDataObj.save()

        elif request.POST.get('reset'):
            examDataObj = ExamData.objects.get(semester=semester, exam=ca, subject_id=subject)
            examDataObj.allow_test = True
            examDataObj.save()
            resultObj = Result.objects.filter(department=request.session['department'], semester=semester, exam=ca,
                                              subject_id=subject.id)
            ca = int(ca)
            print(ca)
            for obj in resultObj:
                if ca == 1:
                    obj.ca1_marks = 0

                elif ca == 2:
                    obj.ca2_marks = 0

                elif ca == 3:
                    obj.ca3_marks = 0

                elif ca == 4:
                    obj.ca4_marks = 0

                obj.exam_done = False
                obj.save()

        return render(request, 'question.html',
                      {'questions': questions, 'ca': ca, 'semester': semester, 'subject': subject})
    return render(request, 'question.html',
                  {'questions': questions, 'ca': ca, 'semester': semester, 'subject': subject})


from .models import Student


def admission(request):
    if request.POST:
        user = Student()
        # personal information,first and last name
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')

        user.first_name = first_name
        user.last_name = last_name
        user.date_of_birth = dob
        user.gender = gender

        # Present and permanent Address, contact no
        present_address = request.POST.get('present_address')
        permanent_address = request.POST.get('permanent_address')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')

        user.present_address = present_address
        user.permanent_address = permanent_address
        user.contact_no = contact_no
        user.email = email

        # fathers name and contact no,email,blood group,
        fathers_name = request.POST.get('fathers_name')
        fathers_contact_no = request.POST.get('fathers_contact_no')
        fathers_email = request.POST.get('fathers_email')
        blood_group = request.POST.get('blood_group')

        user.fathers_name = fathers_name
        user.fathers_contact_no = fathers_contact_no
        user.fathers_email = fathers_email
        user.blood_group = blood_group

        # Guardian name, contact no. and phone
        guardian_name = request.POST.get('guardian_name')
        guardian_contact_no = request.POST.get('guardian_contact_no')
        relation_with_guardian = request.POST.get('relation_with_guardian')
        cast = request.POST.get('cast')

        user.guardian_name = guardian_name
        user.guardian_contact_no = guardian_contact_no
        user.relation_with_guardian = relation_with_guardian
        user.cast = cast

        # Admission category, Entrance type, rank, and aadhar no.
        admission_cat = request.POST.get('admission_cat')
        entrance_type = request.POST.get('entrance_type')
        rank = request.POST.get('rank')
        aadhar_no = request.POST.get('aadhar_no')

        user.admission_category = admission_cat
        user.entrance_type = entrance_type
        user.rank = rank
        user.aadhar_no = aadhar_no

        # Admission category, Entrance type, rank, and aadhar no.
        school_name_10 = request.POST.get('school_name_10')
        locality_10 = request.POST.get('locality_10')
        medium_10 = request.POST.get('medium_10')
        board_10 = request.POST.get('board_10')

        user.school_name_10 = school_name_10
        user.locality_10 = locality_10
        user.medium_10 = medium_10
        user.board_10 = board_10

        # 10th total, marks,percentage,year
        total_10 = request.POST.get('total_10')
        marks_10 = request.POST.get('marks_10')
        percentage_10 = request.POST.get('percentage_10')
        passing_year_10 = request.POST.get('passing_year_10')

        user.total_10 = total_10
        user.marks_10 = marks_10
        user.percentage_10 = percentage_10
        user.passing_year_10 = passing_year_10

        diploma_or_12 = request.POST.get('diploma_or_12')
        if diploma_or_12 == '12th':
            # 12th school name, locality,medium,board
            school_name_12 = request.POST.get('school_name_12')
            locality_12 = request.POST.get('locality_12')
            medium_12 = request.POST.get('medium_12')
            board_12 = request.POST.get('board_12')

            user.school_name_12 = school_name_12
            user.locality_12 = locality_12
            user.medium_12 = medium_12
            user.board_12 = board_12

            # 12th total, marks,percentage,year
            total_12 = request.POST.get('total_12')
            marks_12 = request.POST.get('marks_12')
            percentage_12 = request.POST.get('percentage_12')
            passing_year_12 = request.POST.get('passing_year_12')

            user.total_12 = total_12
            user.marks_12 = marks_12
            user.percentage_12 = percentage_12
            user.passing_year_12 = passing_year_12

        elif diploma_or_12 == 'diploma':
            # diploma school name, locality,medium,board
            school_name_diploma = request.POST.get('school_name_diploma')
            locality_diploma = request.POST.get('locality_diploma')
            medium_diploma = request.POST.get('medium_diploma')
            board_diploma = request.POST.get('board_diploma')

            user.school_name_diploma = school_name_diploma
            user.locality_diploma = locality_diploma
            user.medium_diploma = medium_diploma
            user.board_diploma = board_diploma

            # diploma total, marks,percentage,year
            total_diploma = request.POST.get('total_diploma')
            marks_diploma = request.POST.get('marks_diploma')
            percentage_diploma = request.POST.get('percentage_diploma')
            passing_year_diploma = request.POST.get('passing_year_diploma')

            user.total_diploma = total_diploma
            user.marks_diploma = marks_diploma
            user.percentage_diploma = percentage_diploma
            user.passing_year_diploma = passing_year_diploma

        elif diploma_or_12 == 'both':
            # 12th school name, locality,medium,board
            school_name_12 = request.POST.get('school_name_12')
            locality_12 = request.POST.get('locality_12')
            medium_12 = request.POST.get('medium_12')
            board_12 = request.POST.get('board_12')

            user.school_name_12 = school_name_12
            user.locality_12 = locality_12
            user.medium_12 = medium_12
            user.board_12 = board_12

            # 12th total, marks,percentage,year
            total_12 = request.POST.get('total_12')
            marks_12 = request.POST.get('marks_12')
            percentage_12 = request.POST.get('percentage_12')
            passing_year_12 = request.POST.get('passing_year_12')

            user.total_12 = total_12
            user.marks_12 = marks_12
            user.percentage_12 = percentage_12
            user.passing_year_12 = passing_year_12

            # diploma school name, locality,medium,board
            school_name_diploma = request.POST.get('school_name_diploma')
            locality_diploma = request.POST.get('locality_diploma')
            medium_diploma = request.POST.get('medium_diploma')
            board_diploma = request.POST.get('board_diploma')

            user.school_name_diploma = school_name_diploma
            user.locality_diploma = locality_diploma
            user.medium_diploma = medium_diploma
            user.board_diploma = board_diploma

            # diploma total, marks,percentage,year
            total_diploma = request.POST.get('total_diploma')
            marks_diploma = request.POST.get('marks_diploma')
            percentage_diploma = request.POST.get('percentage_diploma')
            passing_year_diploma = request.POST.get('passing_year_diploma')

            user.total_diploma = total_diploma
            user.marks_diploma = marks_diploma
            user.percentage_diploma = percentage_diploma
            user.passing_year_diploma = passing_year_diploma
        else:
            msg = 'Please select 12th or Diploma'
            color = 'danger'
            return render(request, 'admission.html', {'msg': msg, 'color': color})
        gap = request.POST.get('gap')
        reason = request.POST.get('reason')

        user.gap = gap
        user.reason = reason
        user.save()

        # print('percentage_diploma', percentage_diploma)
        # print('passing_year_diploma', passing_year_diploma)

        msg = 'submitted successfully'
        color = 'success'
        return render(request, 'admission.html', {'msg': msg, 'color': color})
    return render(request, 'admission.html')


from .models import Admission

from django.db import *


def new_enrollment(request):
    if request.POST:
        # try:
        if request.POST.get('email'):
            try:
                enrollment_no = request.user.enrollment_no

                user = Admission()
                user.year = str(datetime.datetime.today().year)
                user.student_data = Account.object.get(email=request.user.email)
                user.enrollment_no = enrollment_no

                user.email = request.user.email
                user.contact_no = request.POST.get('contact_no')

                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.dob = request.POST.get('dob')
                user.gender = request.POST.get('gender')

                user.address = request.POST.get('address')
                user.city = request.POST.get('city')
                user.state = request.POST.get('state')
                user.country = request.POST.get('country')

                user.fathers_name = request.POST.get('fathers_name')
                user.mothers_name = request.POST.get('mothers_name')
                user.blood_group = request.POST.get('blood_group')
                user.mothers_tongue = request.POST.get('mothers_tongue')

                user.fathers_contact_no = request.POST.get('fathers_contact_no')
                user.guardian_name = request.POST.get('guardian_name')
                user.guardian_contact_no = request.POST.get('guardian_contact_no')
                user.relation_with_guardian = request.POST.get('relation_with_guardian')

                user.nationality = request.POST.get('nationality')
                user.cast = request.POST.get('cast')
                user.religion = request.POST.get('religion')
                user.physically_challenge = request.POST.get('physically_challenge')

                user.department = request.POST.get('department')
                user.aadhar_card_no = request.POST.get('aadhar_card_no')
                user.save()

                user.physically_certificate = request.FILES.get('physically_certificate')
                user.cast_certificate = request.FILES.get('cast_certificate')
                user.photo = request.FILES.get('photo')
                user.aadhar_card = request.FILES.get('aadhar_card')

                user.saveQrCode(enrollment_no=enrollment_no)
                user.save()
                msg = "Saved successfully"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                if Admission.objects.filter(email=request.user.email).count():
                    msg = "Fill Entrance Examination field"
                    color = 'danger'
                    return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
                else:
                    msg = "Try fill all the filed"
                    color = 'danger'
                    return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
        elif request.POST.get('admission_cat'):
            try:
                user = Admission.objects.get(email=request.user.email)
                user.admission_cat = request.POST.get('admission_cat')
                user.conducted_by = request.POST.get('conducted_by')
                user.rank = request.POST.get('rank')
                user.roll_no = request.POST.get('roll_no')

                user.allotment = request.POST.get('allotment')
                user.admit_card = request.FILES.get('admit_card')
                user.rank_card = request.FILES.get('rank_card')
                user.roll_no = request.POST.get('roll_no')
                user.save()
                msg = "Saved successfully And Fill Education information 10th"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                msg = "Entrance examination fill all field"
                color = 'danger'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
        elif request.POST.get('school_name_10'):
            try:
                user = Admission.objects.get(email=request.user.email)
                user.school_name_10 = request.POST.get('school_name_10')
                user.board_10 = request.POST.get('board_10')
                user.medium_10 = request.POST.get('medium_10')

                user.address10 = request.POST.get('address10')
                user.city10 = request.POST.get('city10')
                user.state10 = request.POST.get('state10')
                user.country10 = request.POST.get('country10')
                user.passing_year_10 = request.POST.get('passing_year_10')

                user.sub1 = request.POST.get('sub1')
                user.sub2 = request.POST.get('sub2')
                user.sub3 = request.POST.get('sub3')
                user.sub4 = request.POST.get('sub4')
                user.sub5 = request.POST.get('sub5')
                user.aggregate10 = request.POST.get('aggregate10')

                user.mark10 = request.FILES.get('mark10')
                user.admit10 = request.FILES.get('admit10')
                user.certificate10 = request.FILES.get('certificate10')
                user.save()
                msg = "Saved successfully And Fill 12th or Diploma form"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                msg = "Fill Education information 10th all field correctly"
                color = 'danger'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
        elif request.POST.get('diploma_or_12') == '12th':
            try:
                user = Admission.objects.get(email=request.user.email)
                user.school_name_12 = request.POST.get('school_name_12')
                user.board_12 = request.POST.get('board_12')
                user.medium_12 = request.POST.get('medium_12')

                user.address12 = request.POST.get('address12')
                user.city12 = request.POST.get('city12')
                user.state12 = request.POST.get('state12')
                user.country12 = request.POST.get('country12')
                user.passing_year_12 = request.POST.get('passing_year_12')

                user.english = request.POST.get('english')
                user.chemistry = request.POST.get('chemistry')
                user.physics = request.POST.get('physics')
                user.math = request.POST.get('math')
                user.optional = request.POST.get('optional')
                user.aggregate12 = request.POST.get('aggregate12')

                user.mark12 = request.FILES.get('mark12')
                user.admit12 = request.FILES.get('admit12')
                user.certificate12 = request.FILES.get('certificate12')
                user.save()
                msg = "Saved successfully And Fill others form"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                msg = "Fill Education 12th or Diploma"
                color = 'danger'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
        elif request.POST.get('diploma_or_12') == 'diploma':
            try:
                user = Admission.objects.get(email=request.user.email)
                user.school_name_diploma = request.POST.get('school_name_diploma')
                user.board_diploma = request.POST.get('board_diploma')
                user.medium_diploma = request.POST.get('medium_diploma')

                user.addressDiploma = request.POST.get('addressDiploma')
                user.cityDiploma = request.POST.get('cityDiploma')
                user.stateDiploma = request.POST.get('stateDiploma')
                user.countryDiploma = request.POST.get('countryDiploma')
                user.passing_year_Diploma = request.POST.get('passing_year_Diploma')

                user.marksDiploma = request.POST.get('marksDiploma')
                user.aggregateDiploma = request.POST.get('aggregateDiploma')
                user.division = request.POST.get('division')
                user.markDiploma = request.FILES.get('markDiploma')
                user.certificateDiploma = request.FILES.get('certificateDiploma')
                user.save()
                msg = "Saved successfully And Fill others form"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                msg = "Fill Education 12th or Diploma"
                color = 'danger'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
        elif request.POST.get('loan'):
            try:
                user = Admission.objects.get(email=request.user.email)
                user.loan = request.POST.get('loan')
                user.gap = request.POST.get('gap')
                user.reason = request.POST.get('reason')
                user.hostel = request.POST.get('hostel')
                user.save()
                msg = "Saved successfully"
                color = 'success'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})
            except:
                msg = "Try fill all fields"
                color = 'danger'
                return render(request, 'new_enrollment.html', {'msg': msg, 'color': color})

    return render(request, 'new_enrollment.html')


def export_admission_pdf(request, email):
    user = Admission.objects.get(email=email)
    year = datetime.datetime.today().year

    template_path = 'export_admission_pdf.html'
    context = {'user': user, 'year': year}

    response = render_to_pdf(template_path, context, name=(user.first_name + user.last_name))
    return response

    return render(request, 'pdf_output.html', {'users': user})


def admission_data(request):
    user = Admission.objects.all()
    if request.POST:
        add_user = Account.object.get(email=request.POST.get('email'))
        request.session['student_email'] = request.POST.get('email')
        admission_user = Admission.objects.get(email=request.session['student_email'])

        user = Student()
        user.semester = 1
        user.year = admission_user.year
        user.student_data = add_user
        user.enrollment_no = add_user.enrollment_no
        user.email = add_user.email
        user.contact_no = admission_user.contact_no

        user.first_name = admission_user.first_name
        user.last_name = admission_user.last_name
        user.dob = admission_user.dob
        user.gender = admission_user.gender

        user.address = admission_user.address
        user.city = admission_user.city
        user.state = admission_user.state
        user.country = admission_user.country

        user.fathers_name = admission_user.fathers_name
        user.mothers_name = admission_user.mothers_name
        user.blood_group = admission_user.blood_group
        user.mothers_tongue = admission_user.mothers_tongue

        user.fathers_contact_no = admission_user.fathers_contact_no
        user.guardian_name = admission_user.guardian_name
        user.guardian_contact_no = admission_user.guardian_contact_no
        user.relation_with_guardian = admission_user.relation_with_guardian

        user.nationality = admission_user.nationality
        user.cast = admission_user.cast
        user.religion = admission_user.religion
        user.physically_challenge = admission_user.physically_challenge

        user.department = admission_user.department
        user.aadhar_card_no = admission_user.aadhar_card_no
        # user.save()

        user.physically_certificate = admission_user.physically_certificate
        user.cast_certificate = admission_user.cast_certificate
        user.photo = admission_user.photo
        user.aadhar_card = admission_user.aadhar_card

        user.saveQrCode(enrollment_no=add_user.enrollment_no)

        # user = Student.objects.get(email=request.session['student_email'])
        user.admission_cat = admission_user.admission_cat
        user.conducted_by = admission_user.conducted_by
        user.rank = admission_user.rank
        user.roll_no = admission_user.roll_no

        user.allotment = admission_user.allotment
        user.admit_card = admission_user.admit_card
        user.rank_card = admission_user.rank_card
        user.roll_no = admission_user.roll_no
        # user.save()

        # user = Student.objects.get(email=request.session['student_email'])
        user.school_name_10 = admission_user.school_name_10
        user.board_10 = admission_user.board_10
        user.medium_10 = admission_user.medium_10

        user.address10 = admission_user.address10
        user.city10 = admission_user.city10
        user.state10 = admission_user.state10
        user.country10 = admission_user.country10
        user.passing_year_10 = admission_user.passing_year_10

        user.sub1 = admission_user.sub1
        user.sub2 = admission_user.sub2
        user.sub3 = admission_user.sub3
        user.sub4 = admission_user.sub4
        user.sub5 = admission_user.sub5
        user.aggregate10 = admission_user.aggregate10

        user.mark10 = admission_user.mark10
        user.admit10 = admission_user.admit10
        user.certificate10 = admission_user.certificate10
        # user.save()

        # user = Student.objects.get(email=request.session['student_email'])
        user.school_name_12 = admission_user.school_name_12
        user.board_12 = admission_user.board_12
        user.medium_12 = admission_user.medium_12

        user.address12 = admission_user.address12
        user.city12 = admission_user.city12
        user.state12 = admission_user.state12
        user.country12 = admission_user.country12
        user.passing_year_12 = admission_user.passing_year_12

        user.english = admission_user.english
        user.chemistry = admission_user.chemistry
        user.physics = admission_user.physics
        user.math = admission_user.math
        user.optional = admission_user.optional
        user.aggregate12 = admission_user.aggregate12

        user.mark12 = admission_user.mark12
        user.admit12 = admission_user.admit12
        user.certificate12 = admission_user.certificate12
        # user.save()

        # user = Student.objects.get(email=request.session['student_email'])
        user.school_name_diploma = admission_user.school_name_diploma
        user.board_diploma = admission_user.board_diploma
        user.medium_diploma = admission_user.medium_diploma

        user.addressDiploma = admission_user.addressDiploma
        user.cityDiploma = admission_user.cityDiploma
        user.stateDiploma = admission_user.stateDiploma
        user.countryDiploma = admission_user.countryDiploma
        user.passing_year_Diploma = admission_user.passing_year_Diploma

        user.marksDiploma = admission_user.marksDiploma
        user.aggregateDiploma = admission_user.aggregateDiploma
        user.division = admission_user.division
        user.markDiploma = admission_user.markDiploma
        user.certificateDiploma = admission_user.certificateDiploma
        # user.save()

        # user = Student.objects.get(email=request.session['student_email'])
        user.loan = user.loan
        user.gap = user.gap
        user.reason = user.reason
        user.hostel = user.hostel
        user.save()
        add_user.is_approved = True
        add_user.save()

        new_student = Admission.objects.all()
        return render(request, 'admission_data.html', {'user': new_student, 'YEAR': YEARS})

    return render(request, 'admission_data.html', {'user': user, 'YEAR': YEARS})
