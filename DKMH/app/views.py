from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import random
import string
from django.shortcuts import render,redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from .forms import ForgotPasswordForm 
from .models import Student, Staff
from .serializers import (
    CreateStaffSerializer,
    CreateStudentSerializer,
    SendEmailSerializer  # Nếu bạn muốn giữ action send_email, có thể dùng serializer này
)

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
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return HttpResponse("<h1>Welcome to the homepage!</h1>")


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
                return Response({"message": "Đăng nhập thành công", "username": user.username})
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
    """
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create_staff':
            return CreateStaffSerializer
        elif self.action == 'create_student':
            return CreateStudentSerializer
        elif self.action == 'send_email':
            return SendEmailSerializer
        return None

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if not serializer_class:
            raise NotImplementedError(f"No serializer for action '{self.action}'")
        return serializer_class(*args, **kwargs)

    def list(self, request):
        return Response({
            "message": "Admin Manager: Chọn action create_staff, create_student, send_email, v.v."
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

            # Sinh staffCode và password plaintext
            staff_code = generate_account_code(prefix, Staff, 'staffCode')
            password = generate_password()

            # Tạo Staff (password được hash trong DB)
            staff = Staff.objects.create_user(
                username=staff_code,
                password=password,
                email=email,
                staffCode=staff_code,
                staffName=staff_name
            )

            # Gửi email ngay với mật khẩu gốc
            subject = "Thông tin tài khoản đăng nhập"
            message = (
                f"Xin chào {staff.fullName},\n"
                f"Tài khoản của bạn:\nUsername: {staff.username}\nPassword: {password}"
            )
            send_mail(subject, message, settings.EMAIL_HOST_USER, [staff.email])

            # Đánh dấu đã gửi email
            staff.is_email_sent = True
            staff.save()

            result_data = {
                "prefix": prefix,
                "email": email,
                "staffName": staff_name,
                "staffCode": staff_code,
                "password": password,  # plaintext trả về response
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

            # Sinh studentCode và password plaintext
            student_code = generate_account_code(prefix, Student, 'studentCode')
            password = generate_password()

            # Tạo Student (password được hash)
            student = Student.objects.create_user(
                username=student_code,
                password=password,
                email=email,
                studentCode=student_code,
                fullName=full_name
            )

            # Gửi email với mật khẩu gốc
            subject = "Thông tin tài khoản đăng nhập"
            message = (
                f"Xin chào {student.fullName},\n"
                f"Tài khoản của bạn:\nUsername: {student.username}\nPassword: {password}"
            )
            send_mail(subject, message, settings.EMAIL_HOST_USER, [student.email])

            # Đánh dấu đã gửi email
            student.is_email_sent = True
            student.save()

            result_data = {
                "prefix": prefix,
                "email": email,
                "fullName": full_name,
                "studentCode": student_code,
                "password": password,  # plaintext
            }
            return Response(result_data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=False)
    def send_email(self, request):
        """
        Action tùy chọn: Liệt kê user chưa gửi email (GET).
        POST -> Gửi email cho user chưa gửi.
        (Với cách này, nếu bạn đã gửi email khi tạo, phần này sẽ không gửi gì.)
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
                   
                    message = (
                        f"Xin chào {user.fullName},\n"
                        f"Tài khoản của bạn:\nUsername: {user.username}\nPassword: {user.plain_password}"
                    )
                    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
                    user.is_email_sent = True
                    user.save()
                except Exception as e:
                    print(f"Error sending email to {user.email}: {e}")
                    continue
            return Response({"message": "Đã gửi email thành công"})

# View cho trang đăng nhập
def login_view(request):
    # Nếu người dùng đã đăng nhập, chuyển hướng đến trang chính (hoặc dashboard)
    if request.user.is_authenticated:
        return HttpResponse("Bạn đã đăng nhập rồi!")
    # Render trang đăng nhập
    return render(request, 'login.html')
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

