from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAuthAPIView, AdminViewSet

# Tạo router và đăng ký AdminViewSet
router = DefaultRouter()
router.register(r'admin-manager', AdminViewSet, basename='admin-manager')

urlpatterns = [
    # Đăng nhập/đăng xuất cho admin
    path('auth/', AdminAuthAPIView.as_view(), name='admin-auth'),
    
    # Các route của AdminViewSet được gộp tại endpoint /admin-manager/ và các sub-endpoint
    path('', include(router.urls)),
]
