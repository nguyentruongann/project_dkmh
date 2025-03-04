<<<<<<< HEAD
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Student, Staff
import random
import string
=======
# app/serializers.py
from rest_framework import serializers

class CreateStaffSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)  # 2 ký tự đầu
    email = serializers.EmailField()
    staffName = serializers.CharField(max_length=100)
    staffCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64

class CreateStudentSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)
    email = serializers.EmailField()
    fullName = serializers.CharField(max_length=100)
    studentCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

<<<<<<< HEAD
    def validate_email(self, value):
        """
        Kiểm tra email trùng lặp giữa Student và Staff
        """
        if Student.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Student).")
        if Staff.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Staff).")
        return value

    def create(self, validated_data):
        """
        Tạo Student mới với studentCode ngẫu nhiên (2 ký tự đầu do admin nhập, phần còn lại tự tạo).
        """
        # Tạo studentCode ngẫu nhiên
        studentCode = validated_data['prefix'] + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Tạo mật khẩu ngẫu nhiên cho student
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Tạo Student mới
        student = Student.objects.create(
            **validated_data,
            studentCode=studentCode,
            password=password
        )
        
        return student
class CreateStaffSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)  # 2 ký tự đầu
    email = serializers.EmailField()
    staffName = serializers.CharField(max_length=100)
    staffCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

    def validate_email(self, value):
        """
        Kiểm tra email trùng lặp giữa Staff và Student
        """
        if Staff.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Staff).")
        if Student.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Student).")
        return value

    def create(self, validated_data):
        """
        Tạo Staff mới với staffCode ngẫu nhiên (2 ký tự đầu do admin nhập, phần còn lại tự tạo).
        """
        # Tạo staffCode ngẫu nhiên
        staffCode = validated_data['prefix'] + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Tạo mật khẩu ngẫu nhiên cho staff
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Tạo Staff mới
        staff = Staff.objects.create(
            **validated_data,
            staffCode=staffCode,
            password=password
        )
        
        return staff
=======
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64
class SendEmailSerializer(serializers.Serializer):
    """
    Nếu bạn không cần bất kỳ input nào,
    bạn có thể để trống hoặc đặt một message read-only.
    """
<<<<<<< HEAD
    message = serializers.CharField(read_only=True)
=======
    message = serializers.CharField(read_only=True)
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64
