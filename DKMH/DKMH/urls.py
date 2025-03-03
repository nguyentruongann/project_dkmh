from django.contrib import admin
from django.urls import path, include
from app.views import login_view,forgot_password_view, AdminAuthAPIView, AdminViewSet  # Import các view cần thiết từ app

# Tạo router và đăng ký AdminViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'admin-manager', AdminViewSet, basename='admin-manager')

urlpatterns = [
    # Trang admin mặc định của Django
    path('admin/', admin.site.urls),

    # Đăng nhập mặc định sẽ hiển thị login_view ở đường dẫn '/'
    path('', login_view, name='login'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    # Đăng nhập/đăng xuất cho admin
    path('auth/', AdminAuthAPIView.as_view(), name='admin-auth'),

    # Các route của AdminViewSet được gộp tại endpoint /admin-manager/ và các sub-endpoint
    path('admin-manager/', include(router.urls)),  # Tích hợp các URL từ router

    # Đường dẫn cho DRF Browsable API login/logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
