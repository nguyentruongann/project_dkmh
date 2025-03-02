from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Quản lý tài khoản tùy chỉnh
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username là bắt buộc")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)



# Abstract User Model

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username


# Model Sinh viên
# Model Sinh viên
class Student(CustomUser):
    studentId = models.AutoField(primary_key=True)
    studentCode = models.CharField(max_length=50, unique=True)
    fullName = models.CharField(max_length=255)
    birthDate = models.DateField(null=True, blank=True)  # CHO PHÉP NULL
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    className = models.CharField(max_length=50, null=True, blank=True)
    k = models.IntegerField(null=True, blank=True)
    majorId = models.IntegerField(null=True, blank=True)
    departmentId = models.IntegerField(null=True, blank=True)
    is_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.fullName


# Model Nhân viên
class Staff(CustomUser):
    staffId = models.AutoField(primary_key=True)
    staffCode = models.CharField(max_length=50, unique=True)
    staffName = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    birthDate = models.DateField(null=True, blank=True)  # CHO PHÉP NULL
    departmentId = models.IntegerField(null=True, blank=True)
    is_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.staffName

