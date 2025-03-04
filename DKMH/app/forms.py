<<<<<<< HEAD

=======
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64
# app/forms.py
from django import forms

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)
    phoneNumber = forms.CharField(label="Số điện thoại", max_length=15)
    studentCode = forms.CharField(label="Mã Sinh Viên", max_length=50, required=False)
    staffCode = forms.CharField(label="Mã Nhân Viên", max_length=50, required=False)
<<<<<<< HEAD
  
=======
    fullName = forms.CharField(label="Họ Tên", max_length=255)
>>>>>>> d5a643ba0051472ec2f44ef8482b304f4344ed64
