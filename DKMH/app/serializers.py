from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Student, Staff, Subject, Major, Department, CurriculumFramework
import random
import string

class CreateStudentSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)
    email = serializers.EmailField()
    fullName = serializers.CharField(max_length=100)
    studentCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

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
class SendEmailSerializer(serializers.Serializer):
    """
    Nếu bạn không cần bất kỳ input nào,
    bạn có thể để trống hoặc đặt một message read-only.
    """
    message = serializers.CharField(read_only=True)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'



class MajorSerializer(serializers.ModelSerializer):
    departmentId = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True
    )
    departmentName = serializers.CharField(source='department.departmentName', read_only=True)

    class Meta:
        model = Major
        fields = ['majorId', 'majorCode', 'majorName', 'departmentId', 'departmentName']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['departmentId', 'departmentCode', 'departmentName']


class CurriculumFrameworkSerializer(serializers.ModelSerializer):
    subjectId = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        source='subject',
        write_only=True
    )
    subjectName = serializers.CharField(source='subject.subjectName', read_only=True)

    majorId = serializers.PrimaryKeyRelatedField(
        queryset=Major.objects.all(),
        source='major',
        write_only=True
    )
    majorName = serializers.CharField(source='major.majorName', read_only=True)

    class Meta:
        model = CurriculumFramework
        fields = ['curriculumFrameworkId', 'subjectId', 'subjectName', 'majorId', 'majorName', 'semester']
