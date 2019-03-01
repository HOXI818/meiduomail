from django.http import Http404
from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from areas.models import Area
from areas.serializers import AreaSerializer, SubAreaSerializer


# Create your views here.

# GET /areas/(?P<pk>\d+)/
class SubAreasView(RetrieveAPIView):
    # 指定查询集
    queryset = Area.objects.all()
    # 指定序列化器类
    serializer_class = SubAreaSerializer

    # def get(self, request, pk):
    #     """
    #     获取指定地区信息
    #     1. 根据pk查询指定地区的信息
    #     2. 将地区数据序列化并返回(地区下级地区需要进行嵌套序列化)
    #     """
    #     # try:
    #     #     area = Area.objects.get(pk=pk)
    #     # except Area.DoesNotExist:
    #     #     raise Http404
    #     area = self.get_object()
    #
    #     serializer = SubAreaSerializer(area)
    #     return Response(serializer.data)


# GET /areas/
class AreasView(ListAPIView):
    # 制定当前视图所使用管道查询集
    queryset = Area.objects.filter(parent=None)
    # 指定当前视图所使用的序列化器类
    serializer_class = AreaSerializer
    # def get(self, request):
    #     """
    #     获取所有升级地区的信息
    #     1. 查询所有的省级地区的信息
    #     2. 将升级地区的数据序列化并返回
    #     """
    #     areas = self.get_queryset()
    #
    #     serializer = self.get_serializer(areas, many=True)
    #     return Response(serializer.data)
