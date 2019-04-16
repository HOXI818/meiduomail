from django.http import Http404
from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import ViewSet, ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from areas.models import Area
from areas.serializers import AreaSerializer, SubAreaSerializer


# Create your views here.

class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """地区视图集"""
    # queryset = None
    # serializer_class = None

    # 关闭分页
    pagination_class = None

    def get_serializer_class(self):
        """获取视图所使用的序列化器类"""
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer

    def get_queryset(self):
        """获取视图所使用的查询集"""
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()


# GET /areas/(?P<pk>\d+)/
class SubAreasView(RetrieveAPIView):
    # 指定当前视图所使用的查询集
    queryset = Area.objects.all()
    # 指定当前视图所使用的序列化器类
    serializer_class = SubAreaSerializer

    # def get(self, request, pk):
    #     """
    #     获取指定地区的信息:
    #     1. 根据pk查询指定地区的信息
    #     2. 将地区数据序列化并返回(地区下级地区需要进行嵌套序列化)
    #     """
    #     # 1. 根据pk查询指定地区的信息
    #     area = self.get_object()
    #
    #     # 2. 将地区数据序列化并返回(地区下级地区需要进行嵌套序列化)
    #     serializer = self.get_serializer(area)
    #     return Response(serializer.data)


# GET /areas/
class AreasView(ListAPIView):
    # 指定当前视图所使用的查询集
    queryset = Area.objects.filter(parent=None)
    # 指定当前视图所使用的序列化器类
    serializer_class = AreaSerializer

    # def get(self, request):
    #     """
    #     获取所有省级地区的信息:
    #     1. 查询所有省级地区的信息
    #     2. 将省级地区的数据序列化并返回
    #     """
    #     # 1. 查询所有省级地区的信息
    #     areas = self.get_queryset()
    #
    #     # 2. 将省级地区的数据序列化并返回
    #     serializer = self.get_serializer(areas, many=True)
    #     return Response(serializer.data)
