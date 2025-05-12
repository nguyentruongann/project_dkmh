from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Subject, Major, Department, CurriculumFramework
from .serializers import SubjectSerializer, MajorSerializer, DepartmentSerializer, CurriculumFrameworkSerializer
import csv
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser, FormParser


class SubjectViewSet(viewsets.ViewSet):
    """
    API cho các thao tác của Subject:
    - POST /subjects/           : Thêm môn học (addSubject)
    - PUT /subjects/{pk}/       : Chỉnh sửa môn học (editSubject)
    - DELETE /subjects/{pk}/    : Xóa môn học (deleteSubject)
    - GET /subjects/{pk}/count_lecturers/ : Đếm số giảng viên của môn học (countLecturers)
    """

    def list(self, request):
        subjects = Subject.objects.all()
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        subject = get_object_or_404(Subject, pk=pk)
        serializer = SubjectSerializer(subject)
        return Response(serializer.data)

    def create(self, request):
        """
        Endpoint thêm Subject.
        Dữ liệu cần truyền:
            - subjectCode, subjectName, status, theoreticalCredits, practiceCredit, department
        """
        serializer = SubjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Sử dụng phương thức class addSubject đã định nghĩa trong model
        subject = Subject.addSubject(
            subjectCode=data.get('subjectCode'),
            subjectName=data.get('subjectName'),
            status=data.get('status'),
            theoreticalCredits=data.get('theoreticalCredits'),
            practiceCredit=data.get('practiceCredit'),
            department=data.get('department')
        )
        return Response(SubjectSerializer(subject).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_csv(self, request):
        """Thêm nhiều môn học từ file CSV"""
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        subjects = []
        errors = []
        for row in reader:
            try:
                department = get_object_or_404(Department, departmentId=int(row["departmentId"]))
                subject = Subject(
                    subjectCode=row["subjectCode"],
                    subjectName=row["subjectName"],
                    status=row["status"],
                    theoreticalCredits=int(row["theoreticalCredits"]),
                    practiceCredit=int(row["practiceCredit"]),
                    department=department
                )
                subjects.append(subject)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        Subject.objects.bulk_create(subjects)
        return Response({"message": "Subjects added successfully", "errors": errors}, status=status.HTTP_201_CREATED)


    def update(self, request, pk=None):
        """
        Endpoint chỉnh sửa Subject.
        Dữ liệu cập nhật được truyền qua request.data.
        """
        subject = get_object_or_404(Subject, pk=pk)
        # Gọi phương thức editSubject trên instance để cập nhật
        subject.editSubject(**request.data)
        return Response(SubjectSerializer(subject).data)

    def destroy(self, request, pk=None):
        """
        Endpoint xóa Subject.
        """
        subject = get_object_or_404(Subject, pk=pk)
        subject.deleteSubject()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def count_lecturers(self, request, pk=None):
        """
        Endpoint trả về số lượng giảng viên (Lecturer) liên kết với Subject.
        """
        subject = get_object_or_404(Subject, pk=pk)
        count = subject.countLecturers()
        return Response({'count': count})
    

class MajorViewSet(viewsets.ViewSet):
    """
    API cho các thao tác với ngành học (Major):
    - GET /majors/                         : Lấy danh sách ngành học
    - GET /majors/by_department_name/       : Lọc ngành học theo tên khoa
    - GET /majors/{pk}/                     : Lấy chi tiết ngành học
    - POST /majors/                         : Thêm ngành học từ request JSON
    - POST /majors/upload_csv/              : Thêm nhiều ngành học từ file CSV
    - PUT /majors/{pk}/                     : Cập nhật ngành học
    - DELETE /majors/{pk}/                  : Xóa ngành học
    """

    def list(self, request):
        """Lấy danh sách tất cả ngành học"""
        majors = Major.objects.all()
        serializer = MajorSerializer(majors, many=True)
        return Response(serializer.data)
    
    def retrieve(self, pk=None):
        """Lấy thông tin chi tiết một ngành học"""
        major = get_object_or_404(Major, pk=pk)
        serializer = MajorSerializer(major)
        return Response(serializer.data)


    def create(self, request):
        """Thêm ngành học từ request thông thường"""
        serializer = MajorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_csv(self, request):
        """Thêm nhiều ngành học từ file CSV"""
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        majors = []
        errors = []
        for row in reader:
            try:
                department = get_object_or_404(Department, departmentId=int(row["departmentId"]))
                major = Major(
                    majorCode=row["majorCode"],
                    majorName=row["majorName"],
                    department=department
                )
                majors.append(major)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        Major.objects.bulk_create(majors)
        return Response({"message": "Majors added successfully", "errors": errors}, status=status.HTTP_201_CREATED)
    

    def update(self, request, pk=None):
        """Cập nhật thông tin ngành học"""
        major = get_object_or_404(Major, pk=pk)
        serializer = MajorSerializer(major, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, pk=None):
        """Xóa một ngành học"""
        major = get_object_or_404(Major, pk=pk)
        major.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def by_department_name(self, request):
        """Lọc ngành học theo tên khoa"""
        department_name = request.query_params.get('name', '')

        if not department_name:
            return Response({"error": "Missing department name"}, status=status.HTTP_400_BAD_REQUEST)

        departments = Department.objects.filter(departmentName__icontains=department_name)

        if not departments.exists():
            return Response({"message": f"No departments found with name '{department_name}'"}, status=status.HTTP_404_NOT_FOUND)

        majors = Major.objects.filter(department__in=departments)
        serializer = MajorSerializer(majors, many=True)
        return Response(serializer.data)
    

class DepartmentViewSet(viewsets.ViewSet):
    """
    API cho các thao tác với khoa/phòng ban (Department):
    - GET /departments/          : Lấy danh sách khoa
    - POST /departments/         : Thêm khoa từ request JSON
    - POST /departments/upload_csv/ : Thêm nhiều khoa từ file CSV
    """

    def list(self, request):
        """Lấy danh sách tất cả khoa"""
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Lấy thông tin chi tiết một khoa"""
        department = get_object_or_404(Department, pk=pk)
        serializer = DepartmentSerializer(department)
        return Response(serializer.data)

    def create(self, request):
        """Thêm khoa từ request JSON"""
        serializer = DepartmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_csv(self, request):
        """Thêm nhiều khoa từ file CSV"""
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        departments = []
        errors = []
        for row in reader:
            try:
                department = Department(
                    departmentCode=row["departmentCode"],
                    departmentName=row["departmentName"]
                )
                departments.append(department)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        Department.objects.bulk_create(departments)
        return Response({"message": "Departments added successfully", "errors": errors}, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Cập nhật thông tin khoa"""
        department = get_object_or_404(Department, pk=pk)
        serializer = DepartmentSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Xóa một khoa"""
        department = get_object_or_404(Department, pk=pk)
        department.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CurriculumFrameworkViewSet(viewsets.ViewSet):
    """
     API cho các thao tác với CurriculumFramework:
    - GET /curriculums/                              : Lấy danh sách chương trình khung
    - GET /curriculums/by_major_and_semester/       : Lọc chương trình khung theo ngành học và học kỳ
    - POST /curriculums/                            : Thêm chương trình khung từ request JSON
    - POST /curriculums/upload_csv/                 : Thêm nhiều chương trình khung từ file CSV
    - PUT /curriculums/{pk}/                        : Cập nhật chương trình khung
    - DELETE /curriculums/{pk}/                     : Xóa chương trình khung
    """

    def list(self, request):
        """Lấy danh sách tất cả chương trình khung"""
        curriculums = CurriculumFramework.objects.all()
        serializer = CurriculumFrameworkSerializer(curriculums, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Thêm chương trình khung từ request JSON"""
        serializer = CurriculumFrameworkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_csv(self, request):
        """Thêm nhiều chương trình khung từ file CSV"""
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        curriculums = []
        errors = []
        for row in reader:
            try:
                subject = get_object_or_404(Subject, subjectId=int(row["subjectId"]))
                major = get_object_or_404(Major, majorId=int(row["majorId"]))

                curriculum = CurriculumFramework(
                    subject=subject,
                    major=major,
                    semester=int(row["semester"])
                )
                curriculums.append(curriculum)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        CurriculumFramework.objects.bulk_create(curriculums)
        return Response({"message": "Curriculums added successfully", "errors": errors}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """Chỉnh sửa chương trình khung"""
        curriculum = get_object_or_404(CurriculumFramework, pk=pk)
        serializer = CurriculumFrameworkSerializer(curriculum, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, pk=None):
        """Xóa chương trình khung"""
        curriculum = get_object_or_404(CurriculumFramework, pk=pk)
        curriculum.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def by_major_and_semester(self, request):
        """Lọc chương trình khung theo tên ngành học và học kỳ"""
        major_name = request.query_params.get('majorName', '')
        semester = request.query_params.get('semester', '')

        if not major_name or not semester:
            return Response({"error": "Missing majorName or semester"}, status=status.HTTP_400_BAD_REQUEST)

        majors = Major.objects.filter(majorName__icontains=major_name)

        if not majors.exists():
            return Response({"message": f"No majors found with name '{major_name}'"}, status=status.HTTP_404_NOT_FOUND)

        curriculums = CurriculumFramework.objects.filter(major__in=majors, semester=semester)
        serializer = CurriculumFrameworkSerializer(curriculums, many=True)
        return Response(serializer.data)


