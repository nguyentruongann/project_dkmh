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
        if Student.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Student).")
        if Staff.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại trong hệ thống (Staff).")
        return value

    def create(self, validated_data):
        studentCode = validated_data['prefix'] + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        student = Student.objects.create(
            **validated_data,
            studentCode=studentCode,
            password=password
        )
        
        return student

class CreateStaffSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)
    email = serializers.EmailField()
    staffName = serializers.CharField(max_length=100)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    staffCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

    def validate_email(self, value):
        if Staff.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại (Staff).")
        if Student.objects.filter(email=value).exists():
            raise ValidationError(f"Email {value} đã tồn tại (Student).")
        return value

    def create(self, validated_data):
        staffCode = validated_data['prefix'] + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        staff = Staff.objects.create_user(
            username=staffCode,
            password=password,
            email=validated_data['email'],
            staffCode=staffCode,
            staffName=validated_data['staffName'],
            department=validated_data['department']
        )

        return staff

class SendEmailSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)

class CreateDepartmentSerializer(serializers.Serializer):
    departmentName = serializers.CharField(max_length=255)

class CreateMajorSerializer(serializers.Serializer):
    majorName = serializers.CharField(max_length=255)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    majorCode = serializers.CharField(read_only=True)

    def validate_majorName(self, value):
        if Major.objects.filter(majorName=value).exists():
            raise ValidationError(f"Tên ngành {value} đã tồn tại trong hệ thống.")
        return value

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
        fields = ['curriculumFrameworkId', 'subjectId', 'subjectName', 'majorId', 'majorName', 'semester', 'is_mandatory']