from django.contrib import admin
from django.urls import path, include
from app.views import (
    login_view, forgot_password_view, AdminAuthAPIView, AdminViewSet, HomeView,
    view_curriculum, register_subject, view_invoice, admin_curriculum
)
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import DefaultRouter

# Tạo router và đăng ký AdminViewSet
router = DefaultRouter()
router.register(r'admin-manager', AdminViewSet, basename='admin-manager')

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin URL

    # Đăng nhập mặc định sẽ hiển thị login_view ở đường dẫn '/'
    path('', login_view, name='login'),

    # Các đường dẫn khác
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('auth/', AdminAuthAPIView.as_view(), name='admin-auth'),
    
    # Đường dẫn tới trang Home sau khi đăng nhập thành công
    path('home/', HomeView.as_view(), name='home'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # Các đường dẫn khác của Admin
    path('admin-manager/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Các chức năng của sinh viên
    path('curriculum/', view_curriculum, name='curriculum'),
    path('register_subject/', register_subject, name='register_subject'),
    path('view_invoice/', view_invoice, name='view_invoice'),
    
    # Trang quản lý chương trình khung cho admin
    path('admin-curriculum/', admin_curriculum, name='admin_curriculum'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)