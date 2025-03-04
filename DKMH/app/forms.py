
# app/forms.py
from django import forms

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)
    phoneNumber = forms.CharField(label="Số điện thoại", max_length=15)
    studentCode = forms.CharField(label="Mã Sinh Viên", max_length=50, required=False)
    staffCode = forms.CharField(label="Mã Nhân Viên", max_length=50, required=False)
  
