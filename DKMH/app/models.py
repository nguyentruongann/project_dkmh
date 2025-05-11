from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Q, UniqueConstraint
from django.templatetags.static import static
from django.core.exceptions import ValidationError
import os

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
    plain_password = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.plain_password = raw_password
        super().set_password(raw_password)

# Hàm đặt tên ảnh theo staffCode
def staff_profile_picture_path(instance, filename):
    return f'staff_pics/{instance.staffCode}.png'

# Model Nhân viên (Staff/NhanVienKhoa)
class Staff(CustomUser):
    staffId = models.AutoField(primary_key=True)
    staffCode = models.CharField(max_length=50, unique=True)
    staffName = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=False)
    birthDate = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to=staff_profile_picture_path,
        null=True,
        blank=True,
    )
    major = models.ForeignKey(
        'Major',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="associated_staffs"  # Đổi related_name để tránh xung đột
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_staffs"  # Đổi related_name để tránh xung đột
    )
    managed_student = models.ForeignKey(
        'Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managing_staffs"  # Đổi tên trường và related_name
    )
    is_email_sent = models.BooleanField(default=False)

    def get_profile_picture(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return static('IMG/default_avatar.png')

    def save(self, *args, **kwargs):
        try:
            old_instance = Staff.objects.get(pk=self.pk)
            old_picture = old_instance.profile_picture
        except Staff.DoesNotExist:
            old_picture = None

        if Staff.objects.filter(email=self.email).exclude(id=self.id).exists():
            raise ValidationError(f"Email {self.email} đã tồn tại trong hệ thống.")

        super().save(*args, **kwargs)

        if old_picture and old_picture != self.profile_picture:
            if os.path.isfile(old_picture.path):
                os.remove(old_picture.path)

    def __str__(self):
        return self.staffName

    class Meta:
        constraints = [
            UniqueConstraint(fields=["email"], name="unique_staff_email")
        ]

# Hàm đặt tên ảnh theo studentCode
def student_profile_picture_path(instance, filename):
    return f'student_pics/{instance.studentCode}.png'

# Model Sinh viên
class Student(CustomUser):
    studentId = models.AutoField(primary_key=True)
    studentCode = models.CharField(max_length=50, unique=True)
    fullName = models.CharField(max_length=255)
    birthDate = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=False)
    profile_picture = models.ImageField(
        upload_to=student_profile_picture_path,
        null=True,
        blank=True,
    )
    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    className = models.CharField(max_length=50, null=True, blank=True)
    k = models.IntegerField(null=True, blank=True)
    major = models.ForeignKey(
        'Major',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrolled_students"  # Đổi related_name để tránh xung đột
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_students"  # Đổi related_name để tránh xung đột
    )
    is_email_sent = models.BooleanField(default=False)

    def get_profile_picture(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return static('IMG/default_avatar.png')

    def save(self, *args, **kwargs):
        try:
            old_instance = Student.objects.get(pk=self.pk)
            old_picture = old_instance.profile_picture
        except Student.DoesNotExist:
            old_picture = None

        if Student.objects.filter(email=self.email).exclude(id=self.id).exists():
            raise ValidationError(f"Email {self.email} đã tồn tại trong hệ thống.")

        super().save(*args, **kwargs)

        if old_picture and old_picture != self.profile_picture:
            if os.path.isfile(old_picture.path):
                os.remove(old_picture.path)

    def __str__(self):
        return self.fullName

    class Meta:
        constraints = [
            UniqueConstraint(fields=["email"], name="unique_student_email")
        ]

# Model Khoa / Phòng ban
class Department(models.Model):
    departmentId = models.AutoField(primary_key=True)
    departmentCode = models.CharField(max_length=50, unique=True)
    departmentName = models.CharField(max_length=255)

    def __str__(self):
        return self.departmentName

# Model Ngành học
class Major(models.Model):
    majorId = models.AutoField(primary_key=True)
    majorCode = models.CharField(max_length=50, unique=True)
    majorName = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="department_majors"  # Đổi related_name để tránh xung đột
    )

    def __str__(self):
        return self.majorName

# Model Môn học
class Subject(models.Model):
    subjectId = models.AutoField(primary_key=True)
    subjectCode = models.CharField(max_length=50, unique=True)
    subjectName = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    theoreticalCredits = models.IntegerField()
    practiceCredit = models.IntegerField()
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="department_subjects"  # Đổi related_name để tránh xung đột
    )

    def __str__(self):
        return self.subjectName

# Model Giảng viên
class Lecturer(models.Model):
    # Use `id` field instead of `lecturerId` if you want to access `id` directly
    id = models.AutoField(primary_key=True)  # Explicitly set primary key
    lecturerCode = models.CharField(max_length=50, unique=True)
    lecturerName = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    major = models.ForeignKey(
        Major,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="major_lecturers"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="department_lecturers"
    )

    def __str__(self):
        return self.lecturerName

# Model đăng ký học phần của sinh viên
class StudentClass(models.Model):
    studentClassId = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="student_registrations"  # Đổi related_name để tránh xung đột
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="subject_registrations"  # Đổi related_name để tránh xung đột
    )
    registerDate = models.DateField(null=True, blank=True)
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.student.fullName} - {self.subject.subjectName} (Học kỳ {self.semester})"

# Model Thanh toán học phí
class Payment(models.Model):
    paymentId = models.AutoField(primary_key=True)
    paymentCode = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="student_payments"  # Đổi related_name để tránh xung đột
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="subject_payments",
        null=True,
        blank=True  # Đổi related_name để tránh xung đột
    )

    def __str__(self):
        return f"Thanh toán {self.paymentCode} của {self.student.fullName}"

# Model Quản trị viên
class Admin(CustomUser):
    adminId = models.AutoField(primary_key=True)
    adminCode = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

# Model Chương trình khung
class CurriculumFramework(models.Model):
    curriculumFrameworkId = models.AutoField(primary_key=True)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="subject_curriculums"  # Đổi related_name để tránh xung đột
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.CASCADE,
        related_name="major_curriculums"  # Đổi related_name để tránh xung đột
    )
    semester = models.IntegerField()

    def __str__(self):
        return f"Chương trình khung: {self.major.majorName} - {self.subject.subjectName} (Học kỳ {self.semester})"

# Model Lớp
class Class(models.Model):
    classId = models.AutoField(primary_key=True)
    classCode = models.CharField(max_length=50, unique=True)
    className = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="department_classes"  # Đổi related_name để tránh xung đột
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lecturer_classes"  # Đổi related_name để tránh xung đột
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name="subject_classes",  # Đổi related_name để tránh xung đột
        blank=True
    )

    def __str__(self):
        return f"Lớp: {self.className}"