from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet, GenericViewSet

from users.models import User
from users.serializers import UserSerializer, UserDetialSerializer, EmailSerializer, AddressSerializer


# 地址的序列化器类
class AddressViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    # POST /address/
    def create(self, request):
        """
        登录用户地址的新增：
        1. 获取参数并进行校验-参数完整性，手机号格式，邮箱格式
        2. 创建并保存新增地址数据
        3. 将新增地址数据序列化并返回
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)






# PUT /emails/verification/?token=<加密用户的信息>
class EmailVerifyView(APIView):
    def put(self, request):
        """
        用户邮箱验证
        1. 获取token并进行校验 - token必传 token是否有效
        2. 设置对应用户的邮箱验证标记email_active为True
        3. 返回应答,验证成功
        """
        token = request.query_params.get('token')

        if token is None:
            return Response({'message': '缺少token参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 对token进行解密
        user = User.check_email_verify_token(token)

        if user is None:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)


        user.email_active = True
        user.save()


        return Response({'message': 'OK'})

# PUT /email/
class EmailView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self):
        """返回登录用户对象"""
        return self.request.user

    # def put(self, request):
    #     """
    #     登录用户的邮箱设置：
    #     0. 获取登录用户
    #     1. 获取参数并进行校验
    #     2. 设置登录用户的邮箱(update)并且给邮箱发送验证邮件
    #     3. 返回应答，邮箱设置成功
    #     """
    #     user = request.user
    #
    #     serializer = self.get_serializer(user,data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     serializer.save()
    #
    #     return  Response(serializer.data)

# GET /user/
class UserDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetialSerializer

    def get_object(self):
        """返回登录用户对象"""
        return self.request.user

# POST /users/
class UserView(CreateAPIView):
    serializer_class = UserSerializer

    # def post(self, request):
    #     """
    #     注册用户信息保存
    #     1.获取参数进行校验(参数完整性, 用户名不能全部为数字, 是否同意协议,
    #         手机号格式, 手机号是否存在, 两次密码是否一致, 短信验证码是否正确)
    #     2.创建用户病保存到数据库
    #     3.注册成功, 将新用户序列化并返回
    #     """
    #     # 1.获取参数进行校验(参数完整性, 用户名不能全部为数字, 是否同意协议,
    #     #     手机号格式, 手机号是否存在, 两次密码是否一致, 短信验证码是否正确)
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # 2.创建用户病保存到数据库
    #     serializer.save()
    #
    #     # 3.注册成功, 将新用户序列化并返回
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

# GET /usernames/(?P<username>\w{5,20})/count/
class UsernameCountView(APIView):
    def get(self, request, username):
        """
        获取用户数量
        1.根据用户名查询数据库,获取查询结果数量
        2.返回用户名数量
        """
        count = User.objects.filter(username=username).count()

        res_data = {
            'username': username,
            'count':count
        }
        return Response(res_data)

# GET /mobiles/(?P<mobile>1[3-9]\d{9})/count/
class MobileCountView(APIView):
    def get(self, request, mobile):
        """
        获取用户数量
        1.根据手机号查询数据库,获取查询结果数量
        2.返回手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()

        res_data = {
            'mobile': mobile,
            'count':count
        }
        return Response(res_data)