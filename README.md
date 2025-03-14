Dùng xampp :
- start Apache $ MySQL
=> click Admin tại MySQL để mở database trên localhost 
- khởi tạo database "dkmh_db"
---------------------------------------------------------------------------------------------------------------------------
Setting.py :
yêu cầu phải có 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dkmh_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

trong file để xác định database khi chạy code.
---------------------------------------------------------------------------------------------------------------------------
Setting Email host  trong setting.py:
EMAIL_HOST_USER = 'email của bạn'
EMAIL_HOST_PASSWORD = 'mật khẩu ứng dụng của email' 
(quản lý account gmail -> bảo mật-> bật xác minh 2 bước-> kéo xuống dưới cuối)
---------------------------------------------------------------------------------------------------------------------------
Run Terminal :

python manage.py makemigrations
python manage.py migrate  
để đẩy dữ liệu thuộc tính của các class lên database

python manage.py createsuperuser => để tạo account admin

python manage.py runserver  => để chạy server 

click vào đường dẫn trong result của python manage.py runserver để đi đến web.
----------------------------------------------------------------------------------------------------------------------------
Admin :
admin quản lý trong link/admin-manager/
admin chọn tạo account bằng cách login và nhấn vào đường link api khi mới vào web.
tạo 2 kí tự đầu của user
điền email của user
-> sau khi vừa tạo email host sẽ gửi thông tin tài khoản về email user
-----------------------------------------------------------------------------------------------------------------------------