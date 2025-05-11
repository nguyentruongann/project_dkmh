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
    StaffInfoForm, SubjectForm, LecturerForm, StudentUploadForm
)
from .models import Student, Staff, Department, Subject, Lecturer, Major, Class
from .serializers import (
    CreateStaffSerializer, CreateStudentSerializer, SendEmailSerializer,
    CreateDepartmentSerializer, CreateMajorSerializer
)
import pandas as pd

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
        if not Subject.objects.filter(subjectCode=subject_code).exists():
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
                context = {
                    'staff': staff,
                    'avatar_form': StaffAvatarForm(instance=staff),
                    'info_form': StaffInfoForm(instance=staff),
                    'password_form': CustomPasswordChangeForm(user=request.user),
                    'subject_form': SubjectForm(),
                    'lecturer_form': LecturerForm(),
                    'student_upload_form': StudentUploadForm(),
                    'subjects': Subject.objects.all(),
                    'lecturers': Lecturer.objects.all(),
                }
                return render(request, 'staff_home.html', context)
            except Staff.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Staff not found.'})

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
                return render(request, 'error_page.html', {'message': 'Student not found.'})

    def post(self, request):
        username = request.user.username

        if username[:2].isalpha():  # Staff
            # Khởi tạo các biến mặc định
            staff = None
            avatar_form = None
            info_form = None
            password_form = None
            subject_form = SubjectForm()
            lecturer_form = LecturerForm()
            student_upload_form = StudentUploadForm()
            subjects = Subject.objects.all()
            lecturers = Lecturer.objects.all()

            try:
                staff = Staff.objects.get(username=username)
                avatar_form = StaffAvatarForm(instance=staff)
                info_form = StaffInfoForm(instance=staff)
                password_form = CustomPasswordChangeForm(user=request.user)

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
                    subject_form = SubjectForm(request.POST)
                    if subject_form.is_valid():
                        subject = subject_form.save(commit=False)
                        subject.subjectCode = generate_subject_code()
                        subject.save()
                        messages.success(request, 'Môn học đã được thêm.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi thêm môn học.')

                elif 'edit_subject' in request.POST:
                    subject_id = request.POST.get('subject_id')
                    subject = Subject.objects.get(id=subject_id)
                    subject_form = SubjectForm(request.POST, instance=subject)
                    if subject_form.is_valid():
                        subject_form.save()
                        messages.success(request, 'Môn học đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, 'Có lỗi khi sửa môn học.')

                elif 'delete_subject' in request.POST:
                    subject_id = request.POST.get('subject_id')
                    Subject.objects.get(id=subject_id).delete()
                    messages.success(request, 'Môn học đã được xóa.')
                    return redirect('home')

                elif 'add_lecturer' in request.POST:
                    lecturer_form = LecturerForm(request.POST)
                    if lecturer_form.is_valid():
                        lecturer = lecturer_form.save(commit=False)
                        lecturer.lecturerCode = generate_lecturer_code()
                        lecturer.save()
                        messages.success(request, 'Giảng viên đã được thêm.')
                        return redirect('home')
                    messages.error(request, f'Form không hợp lệ: {lecturer_form.errors}')

                elif 'edit_lecturer' in request.POST:
                    lecturer_id = request.POST.get('lecturer_id')
                    lecturer = Lecturer.objects.get(id=lecturer_id)
                    lecturer_form = LecturerForm(request.POST, instance=lecturer)
                    if lecturer_form.is_valid():
                        lecturer_form.save()
                        messages.success(request, 'Giảng viên đã được cập nhật.')
                        return redirect('home')
                    messages.error(request, f'Có lỗi khi sửa giảng viên: {lecturer_form.errors}')

                elif 'delete_lecturer' in request.POST:
                    lecturer_id = request.POST.get('lecturer_id')
                    Lecturer.objects.get(id=lecturer_id).delete()
                    messages.success(request, 'Giảng viên đã được xóa.')
                    return redirect('home')

                elif 'create_students' in request.POST:
                    student_upload_form = StudentUploadForm(request.POST, request.FILES)
                    if student_upload_form.is_valid():
                        excel_file = request.FILES['excel_file']
                        try:
                            df = pd.read_excel(excel_file)
                            print("DataFrame columns:", df.columns.tolist())  # In danh sách cột
                            print("DataFrame data:", df)  # In nội dung DataFrame
                            # Kiểm tra các cột cần thiết
                            required_columns = ['email', 'studentCode', 'fullName', 'k', 'birthDate', 'major', 'className', 'phoneNumber', 'address']
                            missing_columns = [col for col in required_columns if col not in df.columns]
                            if missing_columns:
                                messages.error(request, f'File Excel thiếu các cột: {", ".join(missing_columns)}')
                            else:
                                for index, row in df.iterrows():
                                    print(f"Row {index} type:", type(row))  # In kiểu dữ liệu của row
                                    print(f"Row {index} content:", row)  # In nội dung của row
                                    email = row['email']
                                    prefix = str(row['studentCode'])[:2]  # Lấy 2 ký tự đầu từ studentCode
                                    # Kiểm tra prefix có đúng 2 ký tự không
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
                                    # Tạo hoặc lấy bản ghi Class, đảm bảo classCode là duy nhất
                                    class_defaults = {
                                        'classCode': f"CLASS_{class_name}_{random.randint(1000, 9999)}",  # Tạo classCode duy nhất
                                        'department': major.department
                                    }
                                    class_obj, _ = Class.objects.get_or_create(className=class_name, defaults=class_defaults)

                                    student = Student.objects.create_user(
                                        username=student_code,
                                        password=password,
                                        email=email,
                                        studentCode=student_code,
                                        fullName=full_name,
                                        k=k,
                                        birthDate=birth_date,
                                        major=major,
                                        className=class_name,
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

                context = {
                    'staff': staff,
                    'avatar_form': avatar_form,
                    'info_form': info_form,
                    'password_form': password_form,
                    'subject_form': subject_form,
                    'lecturer_form': lecturer_form,
                    'student_upload_form': student_upload_form,
                    'subjects': subjects,
                    'lecturers': lecturers,
                }
                return render(request, 'staff_home.html', context)

            except Staff.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Staff not found.'})
            except Exception as e:
                messages.error(request, f'Đã xảy ra lỗi: {str(e)}')
                context = {
                    'staff': staff if 'staff' in locals() else None,
                    'avatar_form': avatar_form if 'avatar_form' in locals() else StaffAvatarForm(),
                    'info_form': info_form if 'info_form' in locals() else StaffInfoForm(),
                    'password_form': password_form if 'password_form' in locals() else CustomPasswordChangeForm(user=request.user),
                    'subject_form': subject_form,
                    'lecturer_form': lecturer_form,
                    'student_upload_form': student_upload_form,
                    'subjects': subjects,
                    'lecturers': lecturers,
                }
                return render(request, 'staff_home.html', context)

        else:  # Student
            # Khởi tạo các biến mặc định
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
                return render(request, 'error_page.html', {'message': 'Student not found.'})
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
            raise NotImplementedError(f"No serializer for action '{self.action}'")
        return serializer_class(*args, **kwargs)

    def list(self, request):
        return Response({
            "message": "Admin Manager: Chọn action create_staff, create_student, send_email, create_department, create_major."
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
                    print(f"Error sending email to {user.email}: {e}")
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
        """
        POST -> Tạo Major với mã ngành ngẫu nhiên.
        """
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
    return render(request, 'curriculum.html')

def register_subject(request):
    return render(request, 'register_subject.html')

def view_invoice(request):
    return render(request, 'view_invoice.html')