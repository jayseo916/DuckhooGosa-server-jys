# our setting 2019. 09. 18 THE KOO


from django.urls import path

from django.conf.urls import url, include
# from django.contrib import admin

from rest_framework_mongoengine import routers as merouters
from . import views

# 2단계 route 지점: 여기서도 캐치해서 mongo 리소스는=> views 에 정의한 ToolViewSet 으로 던진다.
merouter = merouters.DefaultRouter()
merouter.register(r'mongo', views.ToolViewSet)
merouter.register(r'comments', views.CommentsViewSet)

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^', include(merouter.urls))
]
