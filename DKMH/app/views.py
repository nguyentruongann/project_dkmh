from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
import random
import string
from django.contrib import messages
from django.shortcuts import render, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse
from .forms import (
    StudentInfoForm, CustomPasswordChangeForm, AvatarForm, StaffAvatarForm,
    StaffInfoForm, SubjectForm, LecturerForm, StudentUploadForm, MajorSemesterForm, 
    CurriculumFrameworkForm, StudentSearchForm
)
from .models import Student, Staff, Department, Subject, Lecturer, Major, Class, CurriculumFramework, StudentClass, Payment, CurriculumSubject
from .serializers import (
    CreateStaffSerializer, CreateStudentSerializer, SendEmailSerializer,
    CreateDepartmentSerializer, CreateMajorSerializer
)
import pandas as pd
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db import models

# Hàm tạo mã ngẫu nhiên
def generate_department_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def generate_account_code(prefix, model, field):
    while True:
        random_part = ''.join(random.choices(string.digits, k=6))
        account_code = f"{prefix}{random_part}"
        if not model.objects.filter(**{field: account_code}).exists():
            return account_code

def generate_lecturer_code():
    while True:
        random_part = ''.join(random.choices(string.digits, k=6))
        lecturer_code = f"GV{random_part}"
        if not Lecturer.objects.filter(lecturerCode=lecturer_code).exists():
            return lecturer_code

def generate_subject_code():
    while True:
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        subject_code = f"MH{random_part}"
        if not CurriculumSubject.objects.filter(subjectCode=subject_code).exists():
            return subject_code

def generate_major_code():
    while True:
        major_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        if not Major.objects.filter(majorCode=major_code).exists():
            return major_code

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Trang chủ (HomeView)
class HomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        username = request.user.username

        if username[:2].isalpha():  # Staff
            try:
                staff = Staff.objects.get(username=username)
                # Lấy danh sách Subject có ít nhất một Class thuộc khoa của staff
                subjects = Subject.objects.filter(
                    subject_classes__department=staff.department,
                    subject_classes__is_nominal=False
                ).distinct()
                context = {
                    'staff': staff,
                    'avatar_form': StaffAvatarForm(instance=staff),
                    'info_form': StaffInfoForm(instance=staff),
                    'password_form': CustomPasswordChangeForm(user=request.user),
                    'subject_form': SubjectForm(staff=staff),
                    'lecturer_form': LecturerForm(staff=staff),
                    'student_upload_form': StudentUploadForm(),
                    'student_search_form': StudentSearchForm(),
                    'subjects': subjects,
                    'lecturers': Lecturer.objects.all(),
                    'searched_students': [],
                }
                return render(request, 'staff_home.html', context)
            except Staff.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Staff không tồn tại.'})

        else:  # Student
            try:
                student = Student.objects.get(username=username)
                context = {
                    'student': student,
                    'info_form': StudentInfoForm(instance=student),
                    'password_form': CustomPasswordChangeForm(user=request.user),
                    'avatar_form': AvatarForm(instance=student),
                }
                return render(request, 'student_home.html', context)
            except Student.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Sinh viên không tồn tại.'})

    def post(self, request):
        username = request.user.username

        if username[:2].isalpha():  # Staff
            staff = None
            avatar_form = None
            info_form = None
            password_form = None
            subject_form = None
            lecturer_form = LecturerForm(staff=None)
            student_upload_form = StudentUploadForm()
            student_search_form = StudentSearchForm()
            subjects = None
            lecturers = Lecturer.objects.all()
            searched_students = []

            try:
                staff = Staff.objects.get(username=username)
                avatar_form = StaffAvatarForm(instance=staff)
                info_form = StaffInfoForm(instance=staff)
                password_form = CustomPasswordChangeForm(user=request.user)
                subject_form = SubjectForm(staff=staff)
                lecturer_form = LecturerForm(staff=staff)
                subjects = Subject.objects.filter(
                    subject_classes__department=staff.department,
                    subject_classes__is_nominal=False
                ).distinct()
                lecturers = Lecturer.objects.all()

                if 'update_avatar' in request.POST:
                    avatar_form = StaffAvatarForm(request.POST, request.FILES, instance=staff)
                    if avatar_form.is_valid():
                        avatar_form.save()
                        messages.success(request, 'Ảnh đại diện đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi cập nhật ảnh đại diện.')

                elif 'update_info' in request.POST:
                    info_form = StaffInfoForm(request.POST, instance=staff)
                    if info_form.is_valid():
                        password = info_form.cleaned_data['password']
                        user = authenticate(username=username, password=password)
                        if user:
                            info_form.save()
                            messages.success(request, 'Thông tin cá nhân đã được cập nhật.')
                            return redirect('home')
                        messages.error(request, 'Mật khẩu không đúng. Vui lòng nhập lại.')
                    messages.error(request, 'Có lỗi khi cập nhật thông tin.')

                elif 'change_password' in request.POST:
                    password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
                    if password_form.is_valid():
                        user = password_form.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Mật khẩu của bạn đã được thay đổi.')
                        return redirect('home')
                    messages.error(request, f'Có lỗi khi đổi mật khẩu: {password_form.errors}')

                elif 'add_subject' in request.POST:
                    subject_form = SubjectForm(request.POST, staff=staff)
                    if subject_form.is_valid():
                        curriculum_subject = subject_form.cleaned_data['curriculum_subject']
                        status = subject_form.cleaned_data['status']
                        max_students = subject_form.cleaned_data['max_students']
                        # Tạo môn học thực tế (Subject) từ môn học tham khảo (CurriculumSubject)
                        real_subject = Subject.objects.create(
                            curriculum_subject=curriculum_subject,
                            status=status,
                            max_students=max_students,
                            current_students=0
                        )
                        class_code = f"CLASS_{curriculum_subject.subjectCode}_{random.randint(1000, 9999)}"
                        class_obj = Class.objects.create(
                            classCode=class_code,
                            className=f"{curriculum_subject.subjectName} - {status}",
                            department=staff.department,
                            subject=real_subject,
                            is_nominal=False
                        )
                        messages.success(request, f'Đã tạo lớp học cho môn {curriculum_subject.subjectName}.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi tạo lớp học.')

                elif 'edit_subject' in request.POST:
                    subject_id = request.POST.get('subject_id')
                    try:
                        subject = Subject.objects.get(subjectId=subject_id)
                        status = request.POST.get('status')
                        max_students = request.POST.get('max_students')

                        # Kiểm tra dữ liệu hợp lệ
                        if status not in [choice[0] for choice in Subject.STATUS_CHOICES]:
                            messages.error(request, 'Trạng thái không hợp lệ.')
                        elif not max_students or int(max_students) < 1:
                            messages.error(request, 'Số lượng sinh viên tối đa phải là một số nguyên dương.')
                        else:
                            subject.status = status
                            subject.max_students = int(max_students)
                            subject.save()
                            messages.success(request, 'Thông tin môn học đã được cập nhật.')
                    except Subject.DoesNotExist:
                        messages.error(request, 'Môn học không tồn tại.')
                    except ValueError:
                        messages.error(request, 'Số lượng sinh viên tối đa phải là một số hợp lệ.')
                    except Exception as e:
                        messages.error(request, f'Có lỗi khi sửa thông tin môn học: {str(e)}')
                    return redirect('home')

                elif 'delete_subject' in request.POST:
                    subject_id = request.POST.get('subject_id')
                    subject = Subject.objects.get(subjectId=subject_id)
                    class_obj = Class.objects.filter(subject=subject, department=staff.department).first()
                    if class_obj:
                        # Xóa các bản ghi StudentClass liên quan trước khi xóa Class
                        StudentClass.objects.filter(class_obj=class_obj).delete()
                        class_obj.delete()
                    subject.delete()
                    messages.success(request, 'Lớp học đã được xóa.')
                    return redirect('home')

                elif 'add_lecturer' in request.POST:
                    lecturer_form = LecturerForm(request.POST, staff=staff)
                    if lecturer_form.is_valid():
                        email = lecturer_form.cleaned_data['email']
                        # Kiểm tra xem giảng viên với email này đã tồn tại hay chưa
                        lecturer = Lecturer.objects.filter(email=email).first()
                        if lecturer:
                            # Nếu giảng viên đã tồn tại, sử dụng bản ghi hiện có
                            class_to_teach = lecturer_form.cleaned_data['class_to_teach']
                            class_to_teach.lecturer = lecturer
                            class_to_teach.save()
                            messages.success(request, f'Giảng viên {lecturer.lecturerName} đã được gán cho lớp {class_to_teach.className}.')
                        else:
                            # Nếu giảng viên chưa tồn tại, tạo mới
                            lecturer = lecturer_form.save(commit=False)
                            lecturer.lecturerCode = generate_lecturer_code()
                            lecturer.save()
                            class_to_teach = lecturer_form.cleaned_data['class_to_teach']
                            class_to_teach.lecturer = lecturer
                            class_to_teach.save()
                            messages.success(request, 'Giảng viên đã được thêm và gán lớp.')
                        return redirect('home')
                    messages.error(request, f'Form không hợp lệ: {lecturer_form.errors}')

                elif 'edit_lecturer' in request.POST:
                    lecturer_id = request.POST.get('lecturer_id')
                    lecturer = Lecturer.objects.get(id=lecturer_id)
                    lecturer_form = LecturerForm(request.POST, instance=lecturer, staff=staff)
                    if lecturer_form.is_valid():
                        class_to_teach = lecturer_form.cleaned_data['class_to_teach']
                        # Kiểm tra xem lớp đã được gán cho giảng viên khác hay chưa
                        if class_to_teach.lecturer and class_to_teach.lecturer != lecturer:
                            messages.error(request, f'Lớp {class_to_teach.className} đã được gán cho giảng viên khác.')
                        else:
                            # Xóa giảng viên khỏi các lớp hiện tại
                            Class.objects.filter(lecturer=lecturer).update(lecturer=None)
                            lecturer_form.save()
                            class_to_teach.lecturer = lecturer
                            class_to_teach.save()
                            messages.success(request, 'Giảng viên đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, f'Có lỗi khi sửa giảng viên: {lecturer_form.errors}')

                elif 'delete_lecturer' in request.POST:
                    lecturer_id = request.POST.get('lecturer_id')
                    lecturer = Lecturer.objects.get(id=lecturer_id)
                    Class.objects.filter(lecturer=lecturer).update(lecturer=None)
                    lecturer.delete()
                    messages.success(request, 'Giảng viên đã được xóa.')
                    return redirect('home')

                elif 'create_students' in request.POST:
                    student_upload_form = StudentUploadForm(request.POST, request.FILES)
                    if student_upload_form.is_valid():
                        excel_file = request.FILES['excel_file']
                        try:
                            df = pd.read_excel(excel_file)
                            required_columns = ['email', 'studentCode', 'fullName', 'k', 'birthDate', 'major', 'className', 'phoneNumber', 'address']
                            missing_columns = [col for col in required_columns if col not in df.columns]
                            if missing_columns:
                                messages.error(request, f'File Excel thiếu các cột: {", ".join(missing_columns)}')
                            else:
                                for index, row in df.iterrows():
                                    email = row['email']
                                    prefix = str(row['studentCode'])[:2]
                                    if len(prefix) != 2:
                                        messages.error(request, f'Hàng {index + 2}: studentCode phải có đúng 2 ký tự (ví dụ: "SV" hoặc "21").')
                                        break
                                    full_name = row['fullName']
                                    k = row['k']
                                    birth_date = row['birthDate']
                                    major_name = row['major']
                                    class_name = row['className']
                                    phone_number = row['phoneNumber']
                                    address = row['address']

                                    student_code = generate_account_code(prefix, Student, 'studentCode')
                                    password = generate_password()

                                    major = Major.objects.get(majorName=major_name)

                                    student = Student.objects.create_user(
                                        username=student_code,
                                        password=password,
                                        email=email,
                                        studentCode=student_code,
                                        fullName=full_name,
                                        k=k,
                                        birthDate=birth_date,
                                        major=major,
                                        className=class_name,  # Chỉ lưu className làm thông tin danh nghĩa
                                        phoneNumber=phone_number,
                                        address=address,
                                        department=major.department,
                                    )

                                    subject = "Thông tin tài khoản đăng nhập"
                                    message = f"Xin chào {student.fullName},\nTài khoản của bạn:\nUsername: {student.username}\nPassword: {password}"
                                    send_mail(subject, message, settings.EMAIL_HOST_USER, [student.email])
                                    student.is_email_sent = True
                                    student.save()

                                messages.success(request, 'Đã tạo tài khoản sinh viên thành công và gửi email.')
                                return redirect('home')
                        except Exception as e:
                            messages.error(request, f'Lỗi khi đọc file Excel: {str(e)}')
                    else:
                        messages.error(request, 'Có lỗi khi tải file Excel.')

                elif 'search_student' in request.POST:
                    student_search_form = StudentSearchForm(request.POST)
                    if student_search_form.is_valid():
                        query = student_search_form.cleaned_data['query']
                        searched_students = Student.objects.filter(
                            models.Q(studentCode__icontains=query) |
                            models.Q(fullName__icontains=query)
                        ).filter(department=staff.department)
                        # Tính toán công nợ cho từng sinh viên
                        students_with_details = []
                        for student in searched_students:
                            total = 0
                            paid = 0
                            accepted_registrations = []
                            for registration in student.student_registrations.all():
                                class_obj = registration.class_obj
                                subject = class_obj.subject
                                if subject.status == 'Chấp Nhận Mở Lớp':
                                    cost = registration.calculate_cost()
                                    payment = class_obj.class_payments.filter(student=student).first()
                                    is_paid = payment.is_paid if payment else False
                                    paid_amount = payment.amount if payment and payment.is_paid else 0
                                    total += cost
                                    paid += paid_amount
                                    accepted_registrations.append({
                                        'registration': registration,
                                        'cost': cost,
                                        'is_paid': is_paid,
                                        'paid_amount': paid_amount,
                                    })
                            students_with_details.append({
                                'student': student,
                                'registrations': accepted_registrations,
                                'total': total,
                                'paid': paid,
                                'debt': total - paid,
                            })
                        searched_students = students_with_details
                        messages.success(request, f'Tìm thấy {len(searched_students)} sinh viên.')
                    else:
                        messages.error(request, 'Vui lòng nhập thông tin tìm kiếm hợp lệ.')

                elif 'cancel_registration' in request.POST:
                    student_id = request.POST.get('student_id')
                    class_id = request.POST.get('class_id')  # Sử dụng class_id thay vì subject_id
                    try:
                        student = Student.objects.get(studentId=student_id)
                        class_obj = Class.objects.get(classId=class_id)
                        registration = StudentClass.objects.filter(student=student, class_obj=class_obj).first()
                        if registration:
                            registration.delete()
                            class_obj.subject.current_students -= 1
                            class_obj.subject.save()
                            messages.success(request, f'Đã hủy đăng ký lớp {class_obj.className} cho sinh viên {student.fullName}.')
                        else:
                            messages.error(request, f'Sinh viên {student.fullName} chưa đăng ký lớp {class_obj.className}.')
                    except Class.DoesNotExist:
                        messages.error(request, 'Lớp học không tồn tại hoặc đã bị xóa.')
                    except Student.DoesNotExist:
                        messages.error(request, 'Sinh viên không tồn tại.')
                    return redirect('home')

                elif 'mark_payment' in request.POST:
                    student_id = request.POST.get('student_id')
                    class_id = request.POST.get('class_id')  # Sử dụng class_id thay vì subject_id
                    try:
                        student = Student.objects.get(studentId=student_id)
                        class_obj = Class.objects.get(classId=class_id)
                        registration = StudentClass.objects.filter(student=student, class_obj=class_obj).first()
                        if registration:
                            payment = Payment.objects.filter(student=student, class_obj=class_obj).first()
                            if not payment:
                                payment_code = f"PAY_{student.studentCode}_{class_obj.classCode}_{random.randint(1000, 9999)}"
                                cost = registration.calculate_cost()
                                payment = Payment.objects.create(
                                    paymentCode=payment_code,
                                    amount=cost,
                                    student=student,
                                    class_obj=class_obj,
                                    is_paid=True
                                )
                            else:
                                payment.is_paid = True
                                payment.save()
                            messages.success(request, f'Đã đánh dấu thanh toán cho lớp {class_obj.className} của sinh viên {student.fullName}.')
                        else:
                            messages.error(request, f'Sinh viên {student.fullName} chưa đăng ký lớp {class_obj.className}.')
                    except Class.DoesNotExist:
                        messages.error(request, 'Lớp học không tồn tại hoặc đã bị xóa.')
                    except Student.DoesNotExist:
                        messages.error(request, 'Sinh viên không tồn tại.')
                    return redirect('home')

                context = {
                    'staff': staff,
                    'avatar_form': avatar_form,
                    'info_form': info_form,
                    'password_form': password_form,
                    'subject_form': subject_form,
                    'lecturer_form': lecturer_form,
                    'student_upload_form': student_upload_form,
                    'student_search_form': student_search_form,
                    'subjects': subjects,
                    'lecturers': lecturers,
                    'searched_students': searched_students,
                }
                return render(request, 'staff_home.html', context)

            except Staff.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Staff không tồn tại.'})
            except Exception as e:
                messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
                context = {
                    'staff': staff if 'staff' in locals() else None,
                    'avatar_form': avatar_form if 'avatar_form' in locals() else StaffAvatarForm(),
                    'info_form': info_form if 'info_form' in locals() else StaffInfoForm(),
                    'password_form': password_form if 'password_form' in locals() else CustomPasswordChangeForm(user=request.user),
                    'subject_form': subject_form if 'subject_form' in locals() else SubjectForm(staff=staff),
                    'lecturer_form': lecturer_form,
                    'student_upload_form': student_upload_form,
                    'student_search_form': student_search_form,
                    'subjects': subjects,
                    'lecturers': lecturers,
                    'searched_students': searched_students,
                }
                return render(request, 'staff_home.html', context)

        else:  # Student
            student = None
            info_form = None
            password_form = None
            avatar_form = None

            try:
                student = Student.objects.get(username=username)
                info_form = StudentInfoForm(instance=student)
                password_form = CustomPasswordChangeForm(user=request.user)
                avatar_form = AvatarForm(instance=student)

                if 'update_avatar' in request.POST:
                    avatar_form = AvatarForm(request.POST, request.FILES, instance=student)
                    if avatar_form.is_valid():
                        avatar_form.save()
                        messages.success(request, 'Ảnh đại diện đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi cập nhật ảnh đại diện.')

                elif 'update_info' in request.POST:
                    info_form = StudentInfoForm(request.POST, instance=student)
                    if info_form.is_valid():
                        info_form.save()
                        messages.success(request, 'Thông tin cá nhân đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi cập nhật thông tin.')

                elif 'change_password' in request.POST:
                    password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
                    if password_form.is_valid():
                        user = password_form.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Mật khẩu của bạn đã được thay đổi.')
                        return redirect('home')
                    messages.error(request, 'Mật khẩu không hợp lệ hoặc không khớp.')

                context = {
                    'student': student,
                    'info_form': info_form,
                    'password_form': password_form,
                    'avatar_form': avatar_form,
                }
                return render(request, 'student_home.html', context)

            except Student.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Sinh viên không tồn tại.'})
            except Exception as e:
                messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
                context = {
                    'student': student if 'student' in locals() else None,
                    'info_form': info_form if 'info_form' in locals() else StudentInfoForm(),
                    'password_form': password_form if 'password_form' in locals() else CustomPasswordChangeForm(user=request.user),
                    'avatar_form': avatar_form if 'avatar_form' in locals() else AvatarForm(),
                }
                return render(request, 'student_home.html', context)

# Đăng nhập/đăng xuất admin
@method_decorator(csrf_exempt, name='dispatch')
class AdminAuthAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"message": "Admin Auth: Sử dụng POST để đăng nhập hoặc đăng xuất."})

    def post(self, request):
        action = request.data.get("action")
        if action == "login":
            username = request.data.get("username")
            password = request.data.get("password")
            user = authenticate(username=username, password=password)
            if user and user.is_staff:
                login(request, user)
                return HttpResponseRedirect(reverse('home'))
            return Response({"error": "Sai thông tin đăng nhập"}, status=status.HTTP_400_BAD_REQUEST)

        elif action == "logout":
            logout(request)
            return Response({"message": "Đăng xuất thành công"})

        return Response({"error": "Hành động không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

# ViewSet quản trị
class AdminViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create_staff':
            return CreateStaffSerializer
        elif self.action == 'create_student':
            return CreateStudentSerializer
        elif self.action == 'send_email':
            return SendEmailSerializer
        elif self.action == 'create_department':
            return CreateDepartmentSerializer
        elif self.action == 'create_major':
            return CreateMajorSerializer
        return None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if not serializer_class:
            raise NotImplementedError(f"Không có serializer cho hành động '{self.action}'")
        return serializer_class(*args, **kwargs)

    def list(self, request):
        return Response({
            "message": "Admin Manager: Chọn action create_staff, create_student, send_email, create_department, create_major, create_curriculum."
        })

    @action(methods=['get', 'post'], detail=False)
    def create_staff(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer()
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            prefix = data['prefix']
            email = data['email']
            staff_name = data['staffName']
            major = data['major']

            staff_code = generate_account_code(prefix, Staff, 'staffCode')
            password = generate_password()

            staff = Staff.objects.create_user(
                username=staff_code,
                password=password,
                email=email,
                staffCode=staff_code,
                staffName=staff_name,
                major=major,
                department=major.department if major else None
            )

            subject = "Thông tin tài khoản đăng nhập"
            message = f"Xin chào {staff.staffName},\nTài khoản của bạn:\nUsername: {staff.username}\nPassword: {password}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [staff.email])

            staff.is_email_sent = True
            staff.save()

            result_data = {
                "prefix": prefix,
                "email": email,
                "staffName": staff_name,
                "major": staff.major.majorName if staff.major else None,
                "staffCode": staff_code,
                "password": password,
            }
            return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def create_student(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer()
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            prefix = data['prefix']
            email = data['email']
            full_name = data['fullName']

            student_code = generate_account_code(prefix, Student, 'studentCode')
            password = generate_password()

            student = Student.objects.create_user(
                username=student_code,
                password=password,
                email=email,
                studentCode=student_code,
                fullName=full_name
            )

            subject = "Thông tin tài khoản đăng nhập"
            message = f"Xin chào {student.fullName},\nTài khoản của bạn:\nUsername: {student.username}\nPassword: {password}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [student.email])

            student.is_email_sent = True
            student.save()

            result_data = {
                "prefix": prefix,
                "email": email,
                "fullName": full_name,
                "studentCode": student_code,
                "password": password,
            }
            return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def send_email(self, request):
        if request.method == 'GET':
            unsent_students = Student.objects.filter(is_email_sent=False).values('id', 'username', 'email', 'is_email_sent')
            unsent_staff = Staff.objects.filter(is_email_sent=False).values('id', 'username', 'email', 'is_email_sent')
            data = {
                "unsent_students": list(unsent_students),
                "unsent_staff": list(unsent_staff)
            }
            return Response(data)
        elif request.method == 'POST':
            users = list(Student.objects.filter(is_email_sent=False)) + list(Staff.objects.filter(is_email_sent=False))
            if not users:
                return Response({"message": "Không có tài khoản nào cần gửi email"})
            for user in users:
                try:
                    subject = "Thông tin tài khoản đăng nhập"
                    message = f"Xin chào {user.fullName},\nTài khoản của bạn:\nUsername: {user.username}\nPassword: {user.plain_password}"
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
                    user.is_email_sent = True
                    user.save()
                except Exception as e:
                    print(f"Lỗi gửi email đến {user.email}: {e}")
                    continue
            return Response({"message": "Đã gửi email thành công"})

    @action(methods=['post'], detail=False)
    def create_department(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        department_name = serializer.validated_data.get('departmentName')
        department_code = generate_department_code()

        department = Department.objects.create(
            departmentName=department_name,
            departmentCode=department_code
        )

        result_data = {
            "departmentName": department_name,
            "departmentCode": department_code,
        }

        return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def create_major(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer()
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            major_name = data['majorName']
            department = data['department']
            major_code = generate_major_code()

            major = Major.objects.create(
                majorName=major_name,
                majorCode=major_code,
                department=department
            )

            result_data = {
                "majorName": major_name,
                "majorCode": major_code,
                "department": major.department.departmentName if major.department else None,
            }

            return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def create_curriculum(self, request):
        return HttpResponseRedirect(reverse('admin_curriculum'))

# Trang quản lý chương trình khung cho Admin
@staff_member_required
def admin_curriculum(request):
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('home')

    major_form = MajorSemesterForm()
    curriculum_form = CurriculumFrameworkForm()
    selected_major = None
    curriculum = None
    semester_data = []

    if request.method == 'POST':
        if 'set_semesters' in request.POST:
            major_form = MajorSemesterForm(request.POST)
            if major_form.is_valid():
                major = major_form.cleaned_data['major']
                total_semesters = major_form.cleaned_data['total_semesters']
                theoretical_credit_price = major_form.cleaned_data['theoretical_credit_price']
                practical_credit_price = major_form.cleaned_data['practical_credit_price']
                major.total_semesters = total_semesters
                major.theoretical_credit_price = theoretical_credit_price
                major.practical_credit_price = practical_credit_price
                major.save()
                messages.success(request, f'Đã cập nhật thông tin ngành {major.majorName}: {total_semesters} kỳ, giá tín chỉ lý thuyết: {theoretical_credit_price}, giá tín chỉ thực hành: {practical_credit_price}.')
                request.session['selected_major_id'] = major.majorId
                return redirect('admin_curriculum')

        elif 'add_subject_to_curriculum' in request.POST:
            selected_major_id = request.session.get('selected_major_id')
            if not selected_major_id:
                messages.error(request, 'Vui lòng chọn ngành trước khi thêm môn học.')
                return redirect('admin_curriculum')

            try:
                selected_major = Major.objects.get(majorId=selected_major_id)
            except Major.DoesNotExist:
                messages.error(request, 'Ngành không tồn tại. Vui lòng chọn lại.')
                del request.session['selected_major_id']
                return redirect('admin_curriculum')

            data = request.POST.copy()
            data['major'] = selected_major.majorId
            curriculum_form = CurriculumFrameworkForm(data)

            if curriculum_form.is_valid():
                subject_name = curriculum_form.cleaned_data['subject_name']
                theoretical_credits = curriculum_form.cleaned_data['theoretical_credits']
                practice_credit = curriculum_form.cleaned_data['practice_credit']
                max_students = curriculum_form.cleaned_data['max_students']
                curriculum_subject = CurriculumSubject.objects.create(
                    subjectCode=generate_subject_code(),
                    subjectName=subject_name,
                    theoreticalCredits=theoretical_credits,
                    practiceCredit=practice_credit,
                    max_students=max_students,
                    department=selected_major.department,
                )
                curriculum = curriculum_form.save(commit=False)
                curriculum.subject = curriculum_subject
                curriculum.major = selected_major
                curriculum.clean()
                curriculum.save()
                messages.success(request, f'Đã thêm môn {curriculum_subject.subjectName} vào chương trình khung (Học kỳ {curriculum.semester}).')
                return redirect('admin_curriculum')
            else:
                messages.error(request, f'Có lỗi khi thêm môn học: {curriculum_form.errors}')

        elif 'edit_curriculum' in request.POST:
            curriculum_id = request.POST.get('curriculum_id')
            curriculum_instance = CurriculumFramework.objects.get(curriculumFrameworkId=curriculum_id)
            curriculum_instance.semester = request.POST.get('semester')
            curriculum_instance.is_mandatory = 'is_mandatory' in request.POST
            curriculum_instance.clean()
            curriculum_instance.save()
            messages.success(request, 'Chương trình khung đã được cập nhật.')
            return redirect('admin_curriculum')

        elif 'delete_curriculum' in request.POST:
            curriculum_id = request.POST.get('curriculum_id')
            curriculum_instance = CurriculumFramework.objects.get(curriculumFrameworkId=curriculum_id)
            curriculum_subject = curriculum_instance.subject
            curriculum_instance.delete()
            curriculum_subject.delete()
            messages.success(request, 'Chương trình khung và môn học đã được xóa.')
            return redirect('admin_curriculum')

    selected_major_id = request.session.get('selected_major_id')
    if selected_major_id:
        try:
            selected_major = Major.objects.get(majorId=selected_major_id)
            curriculum = CurriculumFramework.objects.filter(major=selected_major)
            semesters = range(1, selected_major.total_semesters + 1)
            for semester in semesters:
                curriculum_for_semester = curriculum.filter(semester=semester)
                semester_data.append((semester, curriculum_for_semester))
        except Major.DoesNotExist:
            messages.error(request, 'Ngành không tồn tại. Vui lòng chọn lại.')
            del request.session['selected_major_id']
            selected_major = None

    context = {
        'major_form': major_form,
        'curriculum_form': curriculum_form,
        'selected_major': selected_major,
        'curriculum': curriculum,
        'semester_data': semester_data,
    }
    return render(request, 'admin_curriculum.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, 'login.html', {'error': 'Sai tài khoản hoặc mật khẩu'})
    return render(request, 'login.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        student_code = request.POST.get('studentCode')
        staff_code = request.POST.get('staffCode')

        user = None
        if student_code:
            user = Student.objects.filter(studentCode=student_code, email=email).first()
        elif staff_code:
            user = Staff.objects.filter(staffCode=staff_code, email=email).first()

        if user:
            subject = "Mật khẩu"
            message = f"Chào {user.fullName},\n\nMật khẩu của bạn là: {user.plain_password}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
            return JsonResponse({"status": "success", "message": "Mật khẩu đã được gửi về email của bạn."})
        else:
            return JsonResponse({"status": "error", "message": "Thông tin không chính xác, vui lòng kiểm tra lại."})

    return render(request, 'forgot_password.html')

def view_curriculum(request):
    student = Student.objects.get(username=request.user.username)
    curriculum = CurriculumFramework.objects.filter(major=student.major)
    return render(request, 'curriculum.html', {'curriculum': curriculum, 'student': student})

def register_subject(request):
    student = Student.objects.get(username=request.user.username)
    curriculum = CurriculumFramework.objects.filter(major=student.major)
    # Lấy danh sách lớp học (Class) thay vì môn học (Subject)
    classes = Class.objects.filter(
        subject__curriculum_subject__in=curriculum.values('subject'),
        subject__status__in=['Mở', 'Chấp Nhận Mở Lớp'],
        is_nominal=False
    ).distinct()

    if request.method == 'POST':
        action = request.POST.get('action')
        class_id = request.POST.get('class_id')

        try:
            class_obj = Class.objects.get(classId=class_id)
            subject = class_obj.subject

            if action == 'register':
                if subject.current_students >= subject.max_students:
                    messages.error(request, f'Lớp {class_obj.className} đã đủ số lượng sinh viên.')
                elif StudentClass.objects.filter(student=student, class_obj=class_obj).exists():
                    messages.error(request, f'Bạn đã đăng ký lớp {class_obj.className}.')
                else:
                    StudentClass.objects.create(
                        student=student,
                        class_obj=class_obj,
                        registerDate=timezone.now(),
                        semester=student.k
                    )
                    subject.current_students += 1
                    subject.save()
                    messages.success(request, f'Đăng ký lớp {class_obj.className} thành công.')

            elif action == 'cancel' and subject.status == 'Mở':
                registration = StudentClass.objects.filter(student=student, class_obj=class_obj).first()
                if registration:
                    registration.delete()
                    subject.current_students -= 1
                    subject.save()
                    messages.success(request, f'Hủy đăng ký lớp {class_obj.className} thành công.')
                else:
                    messages.error(request, f'Bạn chưa đăng ký lớp {class_obj.className}.')

            elif action == 'cancel' and subject.status != 'Mở':
                messages.error(request, f'Không thể hủy lớp {class_obj.className} vì trạng thái là {subject.status}.')

        except Class.DoesNotExist:
            messages.error(request, 'Lớp học không tồn tại.')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi: {str(e)}')

        return redirect('register_subject')

    registered_classes = StudentClass.objects.filter(student=student).values_list('class_obj__classId', flat=True)
    return render(request, 'register_subject.html', {
        'student': student,
        'classes': classes,
        'registered_classes': registered_classes,
        'curriculum': curriculum,
    })

def view_invoice(request):
    student = Student.objects.get(username=request.user.username)
    registered_classes = StudentClass.objects.filter(student=student)
    
    total_amount = 0
    paid_amount = 0
    debt = 0
    invoice_details = []

    for registration in registered_classes:
        class_obj = registration.class_obj
        subject = class_obj.subject
        if subject.status == 'Chấp Nhận Mở Lớp':
            cost = registration.calculate_cost()
            payment = Payment.objects.filter(student=student, class_obj=class_obj).first()
            is_paid = payment.is_paid if payment else False
            paid = payment.amount if payment and payment.is_paid else 0
            total_amount += cost
            paid_amount += paid
            invoice_details.append({
                'class_obj': class_obj,
                'cost': cost,
                'is_paid': is_paid,
                'paid_amount': paid,
            })

    debt = total_amount - paid_amount

    context = {
        'student': student,
        'invoice_details': invoice_details,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'debt': debt,
    }
    return render(request, 'view_invoice.html', context)