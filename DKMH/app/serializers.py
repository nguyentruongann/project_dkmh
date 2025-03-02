# app/serializers.py
from rest_framework import serializers

class CreateStaffSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)  # 2 ký tự đầu
    email = serializers.EmailField()
    staffName = serializers.CharField(max_length=100)
    staffCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

class CreateStudentSerializer(serializers.Serializer):
    prefix = serializers.CharField(max_length=2)
    email = serializers.EmailField()
    fullName = serializers.CharField(max_length=100)
    studentCode = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)

class SendEmailSerializer(serializers.Serializer):
    """
    Nếu bạn không cần bất kỳ input nào,
    bạn có thể để trống hoặc đặt một message read-only.
    """
    message = serializers.CharField(read_only=True)
