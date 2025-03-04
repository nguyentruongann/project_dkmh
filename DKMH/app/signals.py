from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Student, Staff, Lecturer, Admin

# Kiểm tra email trùng lặp trước khi lưu bản ghi
@receiver(pre_save, sender=Student)
@receiver(pre_save, sender=Staff)
@receiver(pre_save, sender=Lecturer)
@receiver(pre_save, sender=Admin)
def check_email_duplicate(sender, instance, **kwargs):
    if instance.email:
        # Kiểm tra trùng email giữa tất cả các model
        if sender.objects.filter(email=instance.email).exclude(id=instance.id).exists():
            raise ValidationError(f"Email {instance.email} đã tồn tại.")
