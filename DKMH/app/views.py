from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse,HttpResponseRedirect,HttpResponseForbidden
import random
import string
from django.contrib import messages
from django.shortcuts import render,redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse
from .forms import  StudentInfoForm, CustomPasswordChangeForm, AvatarForm
# from .forms import ForgotPasswordForm 
from .models import Student, Staff,Department
from .serializers import (
    CreateStaffSerializer,
    CreateStudentSerializer,
    SendEmailSerializer ,
    CreateDepartmentSerializer
)
def generate_department_code():
    """Generate a random 12-character department code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
def generate_account_code(prefix, model, field):
    """Tạo mã tài khoản: 2 ký tự prefix + 6 ký tự số, đảm bảo unique."""
    while True:
        random_part = ''.join(random.choices(string.digits, k=6))  # Chỉ lấy số
        account_code = f"{prefix}{random_part}"
        if not model.objects.filter(**{field: account_code}).exists():
            return account_code

def generate_password():
    """Sinh mật khẩu ngẫu nhiên 10 ký tự."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


# Trang chủ đơn giản
class HomeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        username = request.user.username
        
        # Kiểm tra nếu username bắt đầu bằng 2 ký tự chữ => là staff
        if username[:2].isalpha():  # Nếu 2 ký tự đầu là chữ (staff)
            try:
                staff = Staff.objects.get(username=username)
                return render(request, 'staff_home.html', {'staff': staff})
            except Staff.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Staff not found.'})
        
        # Nếu username không phải là staff, xử lý như sinh viên
        else:
            try:
                student = Student.objects.get(username=username)
            except Student.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Student not found.'})

            # Khởi tạo các form cho GET (để hiển thị các dữ liệu hiện tại của sinh viên)
            info_form = StudentInfoForm(instance=student)
            password_form = CustomPasswordChangeForm(user=request.user)
            avatar_form = AvatarForm(instance=student)

            return render(request, 'student_home.html', {
                'student': student,
                'info_form': info_form,
                'password_form': password_form,
                'avatar_form': avatar_form
            })

    def post(self, request):
        username = request.user.username
        
        # Kiểm tra nếu username bắt đầu bằng 2 ký tự chữ => là staff
        if username[:2].isalpha():  # Nếu 2 ký tự đầu là chữ (staff)
            return HttpResponseForbidden('Chức năng này không dành cho staff.')  # Chỉ cho phép sinh viên chỉnh sửa
        
        # Nếu là sinh viên
        else:
            try:
                student = Student.objects.get(username=username)
            except Student.DoesNotExist:
                return render(request, 'error_page.html', {'message': 'Student not found.'})

            # Xử lý form khi có yêu cầu POST
            # Đổi ảnh đại diện
            if 'update_avatar' in request.POST:
                avatar_form = AvatarForm(request.POST, request.FILES, instance=student)
                if avatar_form.is_valid():
                    avatar_form.save()
                    messages.success(request, 'Ảnh đại diện đã được cập nhật.')
                    return redirect('home')  # Reload lại trang

            # Đổi thông tin cá nhân
            elif 'update_info' in request.POST:
                info_form = StudentInfoForm(request.POST, instance=student)
                if info_form.is_valid():
                    info_form.save()
                    messages.success(request, 'Thông tin cá nhân đã được cập nhật.')
                    return redirect('home')

            # Đổi mật khẩu
            elif 'change_password' in request.POST:
                password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
                if password_form.is_valid():
                    user = password_form.save()  # Lưu mật khẩu mới
                    update_session_auth_hash(request, user)  # Cập nhật session sau khi đổi mật khẩu
                    messages.success(request, 'Mật khẩu của bạn đã được thay đổi.')
                    return redirect('home')
                else:
                    messages.error(request, 'Mật khẩu không hợp lệ hoặc không khớp.')

            # Nếu không có trường hợp nào, gửi lại thông báo lỗi
            messages.error(request, 'Dữ liệu không hợp lệ.')
            return redirect('home')
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
                # Đăng nhập thành công, bắt đầu phiên làm việc
                login(request, user)
                # Chuyển hướng đến trang home sau khi đăng nhập thành công
                return HttpResponseRedirect(reverse('home'))  # Chuyển hướng tới trang chủ (Home)
            return Response({"error": "Sai thông tin đăng nhập"}, status=status.HTTP_400_BAD_REQUEST)
        
        elif action == "logout":
            logout(request)
            return Response({"message": "Đăng xuất thành công"})
        
        return Response({"error": "Hành động không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
# ViewSet quản trị
class AdminViewSet(viewsets.ViewSet):
    """
    - GET /admin-manager/ -> list()
    - GET/POST /admin-manager/create_staff/ -> Tạo Staff và gửi email ngay lúc tạo.
    - GET/POST /admin-manager/create_student/ -> Tạo Student và gửi email ngay lúc tạo.
    - (Tùy chọn) GET/POST /admin-manager/send_email/ -> Chỉ hiển thị danh sách user chưa gửi (thường sẽ rỗng).
    - POST /admin-manager/create_department/ -> Tạo Khoa với mã khoa ngẫu nhiên.
    """
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
        return None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if not serializer_class:
            raise NotImplementedError(f"No serializer for action '{self.action}'")
        return serializer_class(*args, **kwargs)

    def list(self, request):
        return Response({
            "message": "Admin Manager: Chọn action create_staff, create_student, send_email, create_department."
        })

    @action(methods=['get', 'post'], detail=False)
    def create_staff(self, request):
        """
        GET -> Hiển thị form (prefix, email, staffName).
        POST -> Tạo Staff, gửi email ngay với mật khẩu gốc, đánh dấu is_email_sent=True.
        """
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

            staff_code = generate_account_code(prefix, Staff, 'staffCode')
            password = generate_password()

            staff = Staff.objects.create_user(
                username=staff_code,
                password=password,
                email=email,
                staffCode=staff_code,
                staffName=staff_name
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
                "staffCode": staff_code,
                "password": password,
            }
            return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def create_student(self, request):
        """
        GET -> Hiển thị form (prefix, email, fullName).
        POST -> Tạo Student, gửi email ngay với mật khẩu gốc, đánh dấu is_email_sent=True.
        """
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
        """
        Action tùy chọn: Liệt kê user chưa gửi email (GET).
        POST -> Gửi email cho user chưa gửi.
        """
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
        """
        POST -> Tạo Khoa với mã khoa ngẫu nhiên.
        """
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
# View cho trang đăng nhập
def login_view(request):
    # Kiểm tra nếu người dùng đã đăng nhập, chuyển hướng đến trang home
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))  # Chuyển hướng đến trang home nếu đã đăng nhập

    # Nếu chưa đăng nhập, hiển thị trang đăng nhập
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))  # Chuyển hướng tới trang home khi đăng nhập thành công
        else:
            # Thông báo lỗi nếu đăng nhập thất bại
            return render(request, 'login.html', {'error': 'Sai tài khoản hoặc mật khẩu'})  # Hiển thị thông báo lỗi

    return render(request, 'login.html')  # Hiển thị form đăng nhập nếu chưa có POST
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        student_code = request.POST.get('studentCode')
        staff_code = request.POST.get('staffCode')

        # Kiểm tra thông tin người dùng: Nếu là sinh viên, kiểm tra mã sinh viên và email
        user = None
        if student_code:
            user = Student.objects.filter(studentCode=student_code, email=email).first()
        elif staff_code:
            user = Staff.objects.filter(staffCode=staff_code, email=email).first()

        if user:
            # Gửi mật khẩu qua email (mật khẩu chưa băm)
            subject = "Mật khẩu"
            message = f"Chào {user.fullName},\n\nMật khẩu của bạn là: {user.plain_password}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

            return JsonResponse({"status": "success", "message": "Mật khẩu đã được gửi về email của bạn."})
        else:
            return JsonResponse({"status": "error", "message": "Thông tin không chính xác, vui lòng kiểm tra lại."})

    return render(request, 'forgot_password.html')

from django.shortcuts import render

# View chương trình khung
def view_curriculum(request):
    # Trả về trang chương trình khung
    # if 1:
        # return render(request,'error.html')
    return render(request, 'curriculum.html')

# View đăng ký học phần
def register_subject(request):
    # Trả về trang đăng ký học phần
    return render(request, 'register_subject.html')

# View xem hóa đơn
def view_invoice(request):
    # Trả về trang xem hóa đơn
    return render(request, 'view_invoice.html')
