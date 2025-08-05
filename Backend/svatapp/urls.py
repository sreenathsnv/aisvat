from django.urls import include, path, re_path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'report', ReportViewSet, basename='report')
router.register(r'code_analysis', CodeAnalysisViewSet, basename='code_analysis')

urlpatterns = [
    path('test/', test),
     path('send-email/', test_email, name='send_email'),
     
     path('', include(router.urls)),
     path('news/', NewsView.as_view(), name='news'),
     path('api-auth/', include('rest_framework.urls')),
      path('results/<str:collection_name>/', ResultView.as_view(), name='result'),
     
     re_path(r'^auth/', include('djoser.urls')),
     re_path(r'^auth/', include('djoser.urls.jwt')),
]
