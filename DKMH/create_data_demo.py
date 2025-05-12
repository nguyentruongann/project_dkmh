import pandas as pd

# Dữ liệu mẫu
data = {
    'email': ['student1@example.com', 'student2@example.com', 'student3@example.com'],
    'studentCode': ['21', '21', '21'],  # Chỉ chứa 2 ký tự
    'fullName': ['Nguyen Van A', 'Tran Thi B', 'Le Van C'],
    'k': [65, 65, 66],
    'birthDate': ['2000-01-01', '2000-02-02', '2001-03-03'],
    'major': ['KHDL', 'KHDL', 'KHDL'],
    'className': ['CNTT01', 'KTPM01', 'KHMT01'],
    'phoneNumber': ['0123456789', '0987654321', '0912345678'],
    'address': ['123 Đường Láng', '456 Đường Giải Phóng', '789 Đường Nguyễn Trãi']
}

# Tạo DataFrame từ dữ liệu
df = pd.DataFrame(data)

# Lưu DataFrame vào file Excel
df.to_excel('student_data_sample.xlsx', index=False)

print("File Excel mẫu 'student_data_sample.xlsx' đã được tạo thành công!")