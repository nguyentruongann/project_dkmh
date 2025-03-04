from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
# ---------------------------
# Quản lý tài khoản tùy chỉnh
# ---------------------------
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


# ---------------------------
# Abstract User Model
# ---------------------------
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
        """Lưu mật khẩu chưa băm và băm mật khẩu khi cần."""
        self.plain_password = raw_password
        super().set_password(raw_password)


# ---------------------------
# Model Sinh viên
# ---------------------------
class Student(CustomUser):
    studentId = models.AutoField(primary_key=True)
    studentCode = models.CharField(max_length=50, unique=True)
    fullName = models.CharField(max_length=255)
    birthDate = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=False)

    phoneNumber = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    className = models.CharField(max_length=50, null=True, blank=True)
    k = models.IntegerField(null=True, blank=True)
    major = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    is_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.fullName
    def save(self, *args, **kwargs):
        # Kiểm tra email trùng lặp trước khi lưu
        if Student.objects.filter(email=self.email).exclude(id=self.id).exists():
            raise ValidationError(f"Email {self.email} đã tồn tại trong hệ thống.")
        super().save(*args, **kwargs)
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["email"],
                name="unique_student_email",
                condition=Q(email__isnull=False)  # Không áp dụng nếu email là NULL
            )
        ]


# ---------------------------
# Model Nhân viên
# ---------------------------
class Staff(CustomUser):
    staffId = models.AutoField(primary_key=True)
    staffCode = models.CharField(max_length=50, unique=True)
    staffName = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=False)

    birthDate = models.DateField(null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name="staffs")
    is_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.staffName
    def save(self, *args, **kwargs):
        # Kiểm tra email trùng lặp trước khi lưu
        if Student.objects.filter(email=self.email).exclude(id=self.id).exists():
            raise ValidationError(f"Email {self.email} đã tồn tại trong hệ thống.")
        super().save(*args, **kwargs)
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["email"],
                name="unique_staff_email",
                condition=Q(email__isnull=False)
            )
        ]
# ---------------------------
# Model Khoa / Phòng ban
# ---------------------------
class Department(models.Model):
    departmentId = models.AutoField(primary_key=True)
    departmentCode = models.CharField(max_length=50, unique=True)
    departmentName = models.CharField(max_length=255)

    def __str__(self):
        return self.departmentName


# ---------------------------
# Model Ngành học
# ---------------------------
class Major(models.Model):
    majorId = models.AutoField(primary_key=True)
    majorCode = models.CharField(max_length=50, unique=True)
    majorName = models.CharField(max_length=255)
    # Liên kết với Department (FK)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="majors")

    def __str__(self):
        return self.majorName


# ---------------------------
# Model Môn học
# ---------------------------
class Subject(models.Model):
    subjectId = models.AutoField(primary_key=True)
    subjectCode = models.CharField(max_length=50, unique=True)
    subjectName = models.CharField(max_length=255)
    status = models.CharField(max_length=50)  # Có thể định nghĩa choices nếu cần
    theoreticalCredits = models.IntegerField()
    practiceCredit = models.IntegerField()
    # Liên kết với Department (FK)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")

    def __str__(self):
        return self.subjectName


# ---------------------------
# Model Giảng viên
# ---------------------------
class Lecturer(models.Model):
    lecturerId = models.AutoField(primary_key=True)
    lecturerCode = models.CharField(max_length=50, unique=True)
    lecturerName = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # Liên kết với Major và Department (FK)
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True, related_name="lecturers")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="lecturers")
    # Quan hệ N-N với Subject
    subjects = models.ManyToManyField(Subject, related_name="lecturers", blank=True)

    def __str__(self):
        return self.lecturerName


# ---------------------------
# Model đăng ký học phần của sinh viên
# ---------------------------
class StudentClass(models.Model):
    studentClassId = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="registrations")
    # Giả sử classId ở đây ám chỉ việc đăng ký một môn học cụ thể
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="registrations")
    registerDate = models.DateField(null=True, blank=True)  # Ngày đăng ký (tùy chọn)
    semester = models.IntegerField()

    def __str__(self):
        return f"{self.student.fullName} - {self.subject.subjectName} (Học kỳ {self.semester})"


# ---------------------------
# Model Thanh toán học phí
# ---------------------------
class Payment(models.Model):
    paymentId = models.AutoField(primary_key=True)
    paymentCode = models.CharField(max_length=50, unique=True)
    amount = models.FloatField()
    # Mỗi lần thanh toán thuộc 1 sinh viên
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    # Tuỳ chọn: thanh toán theo từng môn học
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="payments", null=True, blank=True)

    def __str__(self):
        return f"Thanh toán {self.paymentCode} của {self.student.fullName}"


# ---------------------------
# Model Quản trị viên
# ---------------------------
class Admin(CustomUser):
    adminId = models.AutoField(primary_key=True)
    adminCode = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


# ---------------------------
# Model Chương trình khung
# ---------------------------
class CurriculumFramework(models.Model):
    curriculumFrameworkId = models.AutoField(primary_key=True)
    # Liên kết với Subject và Major
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="curriculums")
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name="curriculums")
    semester = models.IntegerField()

    def __str__(self):
        return f"Chương trình khung: {self.major.majorName} - {self.subject.subjectName} (Học kỳ {self.semester})"