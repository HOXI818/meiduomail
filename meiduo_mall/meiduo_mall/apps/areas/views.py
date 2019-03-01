from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from areas.models import Area
from areas.serializers import AreaSerializer

# Create your views here.


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
