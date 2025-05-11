from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import Student, Lecturer, Staff, Subject, Major, Department, CurriculumFramework

# Form cập nhật thông tin sinh viên
class StudentInfoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['fullName', 'email', 'phoneNumber', 'address', 'birthDate', 'k', 'className', 'department', 'major']
        widgets = {
            'birthDate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Đặt các trường chỉ đọc
        self.fields['k'].widget.attrs['readonly'] = True
        self.fields['className'].widget.attrs['readonly'] = True
        self.fields['department'].widget.attrs['readonly'] = True
        self.fields['major'].widget.attrs['readonly'] = True

# Form đổi mật khẩu (dùng chung cho Student và Staff)
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

    # Tùy chỉnh validation nếu cần giảm bớt yêu cầu
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Mật khẩu mới và xác nhận mật khẩu không khớp.")
        # Nếu muốn bỏ các yêu cầu mặc định của Django, có thể bỏ validate_password
        # validate_password(password2, self.user)  # Bỏ comment nếu muốn giữ validation mặc định
        return password2

# Form đổi ảnh đại diện cho Student
class AvatarForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['profile_picture']

# Form cập nhật ảnh đại diện cho Staff
class StaffAvatarForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['profile_picture']

# Form cập nhật thông tin cá nhân cho Staff
class StaffInfoForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mật khẩu hiện tại")

    class Meta:
        model = Staff
        fields = ['staffName', 'email', 'birthDate', 'address', 'major']
        widgets = {
            'birthDate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['major'].widget.attrs['readonly'] = True

# Form thêm/sửa môn học
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['subjectName', 'theoreticalCredits', 'practiceCredit', 'status', 'department']

# Form thêm/sửa giảng viên
class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = ['lecturerName', 'email', 'major', 'department']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['major'].required = False
        self.fields['department'].required = False

    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance and getattr(self.instance, 'id', None):  # Sửa từ lecturerId thành id
            if Lecturer.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise ValidationError(f"Email {email} đã tồn tại trong hệ thống.")
        else:
            if Lecturer.objects.filter(email=email).exists():
                raise ValidationError(f"Email {email} đã tồn tại trong hệ thống.")
        return email

# Form tải file Excel để tạo sinh viên
class StudentUploadForm(forms.Form):
    excel_file = forms.FileField()