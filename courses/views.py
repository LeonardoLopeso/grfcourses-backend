from rest_framework import viewsets, decorators, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import APIException

from core.utils.exceptions import ValidationError
from core.utils.formatters import format_serializer_error
from courses.filters import CourseFilter
from courses.models import Course, Enrollment, WatchedLesson
from courses.serializers import CourseSerializer, ReviewSerializer

from django.db.models import Avg, Count, Sum

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    filterset_class = CourseFilter # /courses/?price_min="10"
    ordering_fields = ['price', 'created_at'] # /courses/?order="price"

    @decorators.action(detail=True, methods=['get'])
    def reviews(self, request: Request, pk=None):
        course = self.get_object()
        reviews = course.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @decorators.action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_review(self, request: Request, pk=None):
        course = self.get_object()
        user = request.user

        if not Enrollment.objects.filter(user=user, course=course).exists():
            raise APIException("Você precisa estar matriculado neste curso para avaliá-lo.")
        
        if course.reviews.filter(user=user).exists():
            raise APIException(" Vocé ja avaliou este curso.")
        
        data = {
            "rating": request.data.get("rating"),
            "comment": request.data.get("comment")
        }

        serializer = ReviewSerializer(data=data)
        if not serializer.is_valid():
            raise ValidationError(format_serializer_error(serializer.errors))
        
        serializer.save(user=user, course=course)

        aggregate = course.reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id')
        )

        course.average_rating = aggregate['average_rating'] or 0
        course.total_reviews = aggregate['total_reviews'] or 0
        course.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def retrieve(self, request: Request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        enrolled_at = None
        if request.user.is_authenticated:
            enrolled = Enrollment.objects.filter(
                user=request.user,
                course=instance
            ).first()

            if enrolled:
                enrolled_at = enrolled.enrolled_at
            
        return Response({
            **serializer.data,
            'enrolled_at': enrolled_at
        })
    
    @decorators.action(detail=True, methods=['get'])
    def content(self, request: Request, pk=None):
        course = self.get_object()
        
        modules = Module.objects.filter(course=course)
        total_modules = modules.count()

        lessons = Lesson.objects.filter(module__course=course)
        total_lessons = lessons.count()

        total_time = lessons.aggregate(
            total=Sum('time_estimate')
        )['total'] or 0

        watched_lessons_cout = 0
        watched_lessons_set = set()

        if request.user.is_authenticated:
            watched_lessons = WatchedLesson.objects.filter(
                user=request.user,
                lesson__in=lessons
            ).vales_list('lesson_id', flat=True)

            watched_lessons_set = set(watched_lessons)
            watched_lessons_cout = len(watched_lessons_set)
            # Endpoint não finalizado, acompanhar a aula 32 
