from django.contrib import admin
from django.urls import path, include
from app.views import HomeView

urlpatterns = [
    # Trang chủ hiển thị nội dung đơn giản tại URL gốc /
    path('', HomeView.as_view(), name='home'),
    
    # Trang admin mặc định của Django
    path('admin/', admin.site.urls),
    
    # Bao gồm các URL từ ứng dụng (với prefix /app/)
    path('app/', include('app.urls')),
    
    # Đường dẫn cho DRF Browsable API login/logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
