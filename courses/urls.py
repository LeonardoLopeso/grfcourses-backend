from rest_framework.routers import DefaultRouter

from courses.views import CourseViewSet

router = DefaultRouter()
router.register('', CourseViewSet, basename='course')

urlpatterns = router.urls