from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Subject
from .serializers import SubjectSerializer


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

