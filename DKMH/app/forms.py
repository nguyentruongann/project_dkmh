from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import Student, Lecturer, Staff, Subject, Major, Department, CurriculumFramework, Class, CurriculumSubject

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
        self.fields['k'].widget.attrs['readonly'] = True
        self.fields['className'].widget.attrs['readonly'] = True
        self.fields['department'].widget.attrs['readonly'] = True
        self.fields['major'].widget.attrs['readonly'] = True

# Form đổi mật khẩu
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Mật khẩu mới và xác nhận mật khẩu không khớp.")
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

# Form thêm/sửa lớp học cho Staff
class SubjectForm(forms.Form):
    curriculum_subject = forms.ModelChoiceField(queryset=CurriculumSubject.objects.none(), label="Môn học")
    status = forms.ChoiceField(choices=Subject.STATUS_CHOICES, label="Trạng thái")
    max_students = forms.IntegerField(min_value=1, label="Số lượng sinh viên tối đa", initial=30)

    def __init__(self, *args, **kwargs):
        staff = kwargs.pop('staff', None)
        super().__init__(*args, **kwargs)
        if staff and staff.major:
            curriculum_subjects = CurriculumFramework.objects.filter(major=staff.major).values_list('subject', flat=True)
            self.fields['curriculum_subject'].queryset = CurriculumSubject.objects.filter(curriculumSubjectId__in=curriculum_subjects)

# Form thêm/sửa giảng viên
class LecturerForm(forms.ModelForm):
    class Meta:
        model = Lecturer
        fields = ['lecturerName', 'email', 'major', 'department']
    
    class_to_teach = forms.ModelChoiceField(queryset=Class.objects.none(), label="Lớp giảng dạy", required=True)

    def __init__(self, *args, **kwargs):
        staff = kwargs.pop('staff', None)
        super().__init__(*args, **kwargs)
        self.fields['major'].required = False
        self.fields['department'].required = False
        if staff and staff.department:
            # Lấy các lớp chưa có giảng viên
            available_classes = Class.objects.filter(
                department=staff.department,
                is_nominal=False,
                lecturer__isnull=True
            )
            # Nếu đang chỉnh sửa giảng viên, bao gồm lớp hiện tại của giảng viên (nếu có)
            if self.instance and self.instance.pk:
                current_classes = Class.objects.filter(lecturer=self.instance)
                self.fields['class_to_teach'].queryset = available_classes | current_classes
            else:
                self.fields['class_to_teach'].queryset = available_classes

# Form tải file Excel để tạo sinh viên
class StudentUploadForm(forms.Form):
    excel_file = forms.FileField()

# Form chọn ngành và số lượng kỳ
class MajorSemesterForm(forms.Form):
    major = forms.ModelChoiceField(queryset=Major.objects.all(), label="Ngành")
    total_semesters = forms.IntegerField(min_value=1, label="Số lượng kỳ", initial=8)
    theoretical_credit_price = forms.FloatField(min_value=0.0, label="Giá tín chỉ lý thuyết", initial=0.0)
    practical_credit_price = forms.FloatField(min_value=0.0, label="Giá tín chỉ thực hành", initial=0.0)

# Form thêm/sửa chương trình khung cho Admin
class CurriculumFrameworkForm(forms.ModelForm):
    subject_name = forms.CharField(max_length=255, label="Tên môn học")
    theoretical_credits = forms.IntegerField(min_value=0, label="Tín chỉ lý thuyết")
    practice_credit = forms.IntegerField(min_value=0, label="Tín chỉ thực hành")
    max_students = forms.IntegerField(min_value=1, label="Số lượng sinh viên tối đa", initial=30)
    major = forms.ModelChoiceField(queryset=Major.objects.all(), required=False, widget=forms.HiddenInput())

    class Meta:
        model = CurriculumFramework
        fields = ['major', 'semester', 'is_mandatory']
        widgets = {
            'semester': forms.NumberInput(attrs={'min': 1, 'required': 'required'}),
            'is_mandatory': forms.CheckboxInput(),
        }

    def clean_semester(self):
        semester = self.cleaned_data.get('semester')
        if semester is None:
            raise ValidationError("Học kỳ là bắt buộc.")
        if semester <= 0:
            raise ValidationError("Học kỳ phải là một số nguyên dương.")
        return semester

# Form tìm kiếm sinh viên
class StudentSearchForm(forms.Form):
    query = forms.CharField(max_length=255, label="Tìm kiếm sinh viên (mã hoặc tên)", required=False)