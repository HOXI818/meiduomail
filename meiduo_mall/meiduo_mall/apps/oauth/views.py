from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.exceptions import QQAPIError
from oauth.models import OAuthQQUser
from oauth.serializers import QQAuthUserSerializer
from oauth.utils import OAuthQQ
# Create your views here.

# /oauth/qq/user/?code=<code>
class QQAuthUserView(GenericAPIView):
    # 指定当前视图所使用的序列化器类
    serializer_class = QQAuthUserSerializer

    def post(self, request):
        """
        保存QQ登录绑定数据
        1. 获取参数并进行校验
            参数完整性
            手机号格式
            短信验证码是否正确
            access_token是否有效
        2. 保存QQ绑定的数据并生成jwt token
        3. 返回应答，绑定成功
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """
        获取QQ登录用户openid并处理：
        1.获取code并校验（code必传）
        2.获取QQ登录用户的openid
            2.1 通过code请求QQ服务器获取access_token
            2.2 通过access_token请求QQ服务器获取openid
        3.根据openid判断是否绑定过本网站的用户
            3.1 如果已绑定，直接生成jet token并返回
            3.2 如果未绑定，将openid加密并返回
        """
        code = request.query_params.get('code')

        if code is None:
            return Response({'message': '缺少code参数'},status=status.HTTP_400_BAD_REQUEST)

        oauth = OAuthQQ()

        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_openid(access_token)
        except QQAPIError:
            return Response({'message': 'QQ登录异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 已绑定
            secret_openid = OAuthQQ.generate_save_user_token(openid)
            return Response({'access_token': secret_openid})
        else:
            # 未绑定
            user = qq_user.user
            from rest_framework_jwt.settings import api_settings

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)

            token = jwt_encode_handler(payload)

            res_data = {
                'user_id': user.id,
                'username': user.username,
                'token': token
            }
            return Response(res_data)


# GET /oauth/qq/authorization/?next=<登录之后访问页面的地址>
class QQAuthURLView(APIView):
    def get(self, request):
        """
        获取QQ登录网址
        1.获取next
        2.组织QQ登录网址和参数
        3.返回QQ登录网址
        """
        next = request.query_params.get('next', '/')

        oauth = OAuthQQ(state=next)
        login_url = oauth.get_login_url()

        return Response({'login_url': login_url})
