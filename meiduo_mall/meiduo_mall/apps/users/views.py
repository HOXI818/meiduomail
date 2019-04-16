from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet, GenericViewSet

from goods.models import SKU
from goods.serializers import SKUSerializer
from users import constants
from users.models import User
from users.serializers import UserSerializer, UserDetialSerializer, EmailSerializer, AddressSerializer, \
    AddressTitleSerializer, BrowseHistorySerializer


# POST /browse_histories/
class BrowseHistoryView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BrowseHistorySerializer

    # def post(self, request):
    #     """
    #     登录用户浏览记录添加:
    #     1. 获取sku_id并进行校验(sku_id必传，sku_id商品是否存在)
    #     2. 在redis中存储登录用户浏览的记录
    #     3. 返回应答，浏览记录添加成功
    #     """
    #     # 1. 获取sku_id并进行校验(sku_id必传，sku_id商品是否存在)
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # 2. 在redis中存储登录用户浏览的记录(create)
    #     serializer.save()
    #
    #     # 3. 返回应答，浏览记录添加成功
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """
        登录用户浏览记录获取:
        1. 从redis中获取登录用户浏览的商品sku_id
        2. 根据商品sku_id获取对应商品数据
        3. 将商品的数据序列化并返回
        """
        # 获取redis链接对象 StrictRedis
        redis_conn = get_redis_connection('histories')

        # 拼接key
        history_key = 'history_%s' % request.user.id

        # 1. 从redis中获取登录用户浏览的商品sku_id
        # [b'<sku_id>', b'<sku_id>', ...]
        sku_ids = redis_conn.lrange(history_key, 0, -1)

        # 2. 根据商品sku_id获取对应商品数据
        skus = []
        for sku_id in sku_ids:
            # sku = SKU.objects.get(id=b'1')
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        # 3. 将商品的数据序列化并返回
        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)


# 地址的序列化器类
class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # POST /addresses/
    def create(self, request):
        """
        登录用户地址的新增：
        0. 判断用户的地址数量是否超过数量上限
        1. 获取参数并进行校验-参数完整性，手机号格式，邮箱格式
        2. 创建并保存新增地址数据
        3. 将新增地址数据序列化并返回
        """
        count = request.user.addresses.filter(is_deleted=False).count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '地址数量超过上限'}, status=status.HTTP_400_BAD_REQUEST)

        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        #
        # serializer.save()
        #
        # return Response(serializer.data, status=status.HTTP_201_CREATED)

        return super().create(request)

    # GET /addresses/
    def list(self, request):
        """
        获取登录用户地址数据
        1. 获取登录用户所有地址数据
        2. 将地址数据序列化并返回
        """
        addresses = self.get_queryset()

        serializer = self.get_serializer(addresses, many=True)

        user = request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data
        })

    # DELETE /addresses/(?P<pk>\d+)/
    def destroy(self, request, pk):
        """
        删除-逻辑删除-登录用户指定地址
        1. 根据pk获取指定的地址数据
        2. 将地址的is_deleted设置为True
        3. 返回应答
        """
        address = self.get_object()

        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # PUT /addresses/(?P<pk>\d+)/
    # def update(self, request, pk):
    #     """
    #     修改登录用户指定地址
    #     1. 根据pk获取指定的地址数据
    #     2. 获取参数并进行校验
    #     3. 修改指定地址的数据
    #     4. 返回修改地址序列化数据
    #     """
    #     address = self.get_object()
    #
    #     serilazer = self.get_serializer(address, data=request.data)
    #     serilazer.is_valid(raise_exception=True)
    #
    #     serilazer.save()
    #
    #     return Response(serilazer.data)

    # PUT /addresses/(?P<pk>\d+)/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk):
        """
        设置登录用户默认地址
        1.根据pk查询指定的地址
        2.设置登录用户默认地址
        3.返回应答, 设置成功
        """
        address = self.get_object()

        # request.user.default_address = address
        request.user.default_address_id = address.id
        request.user.save()

        return Response({'message':'OK'})

    # PUT /addresses/(?P<pk>\d+)/title/
    @action(methods=['put'], detail=True)
    def title(self,request,pk):
        """
        修改指定地址标题
        1.根据pk查询指定的地址
        2.获取title参数并校验(title必传)
        3.修改指定地址的标题并更新数据库
        4.返回应答,设置标题成功
        """
        address = self.get_object()

        serializer = AddressTitleSerializer(address, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)


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