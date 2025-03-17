# forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Student



# forms.py
from django import forms
from .models import Student

class StudentInfoForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['fullName', 'email', 'phoneNumber', 'address', 'birthDate', 'k','className','department','major']  # Thêm 'k' vào fields
        widgets = {
            'birthDate': forms.DateInput(attrs={'type': 'date'}),  # Định dạng ngày tháng
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Đặt các trường không được thay đổi (readonly)
        self.fields['k'].widget.attrs['readonly'] = True  # Đảm bảo trường 'k' không thể chỉnh sửa
        self.fields['className'].widget.attrs['readonly'] = True
        self.fields['department'].widget.attrs['readonly'] = True
        self.fields['major'].widget.attrs['readonly'] = True

# Form đổi mật khẩu
class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = Student
        fields = ['old_password', 'new_password1', 'new_password2']


# Form đổi ảnh đại diện
class AvatarForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['profile_picture']
