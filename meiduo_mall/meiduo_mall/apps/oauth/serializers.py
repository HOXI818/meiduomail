import base64
import os
import re

from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import OAuthQQ
from users.models import User


class QQAuthUserSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    access_token = serializers.CharField(label='加密openid', write_only=True)
    token = serializers.CharField(label='jwt token', read_only=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$', write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'password', 'sms_code', 'access_token', 'token')

        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }

    # 手机号格式，短信验证码是否正确，access_token是否有效
    # def validate_mobile(self, value):
    #     if not re.match(r'^1[3-9]\d{9}$', value):
    #         raise serializers.ValidationError('手机号格式不正确')
    #
    #     return value

    def validate(self, attrs):
        # access_token是否有效
        access_token = attrs['access_token']

        openid = OAuthQQ.check_save_user_token(access_token)

        if openid is None:
            # 解密失败
            raise serializers.ValidationError('无效的access_token')

        attrs['openid'] = openid

        # 短信验证码是否正确
        mobile = attrs['mobile']

        # 从redis中获取真实的验证码内容
        redis_conn = get_redis_connection('verify_codes')

        real_sms_code = redis_conn.get('sms_%s' % mobile)  # bytes

        if real_sms_code is None:
            raise serializers.ValidationError('短信验证码已失效')

        # 对比验证码内容
        sms_code = attrs['sms_code']  # str

        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        # 如果`mobile`已注册，校验对应的密码是否正确
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 未注册
            user = None
        else:
            # 已注册，校验对应的密码是否正确
            password = attrs['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')

        attrs['user'] = user

        return attrs

    def create(self, validated_data):
        # 如果`mobile`未注册，先创建一个新用户
        user = validated_data['user']

        if user is None:
            mobile = validated_data['mobile']
            password = validated_data['password']
            # 随机生成用户名
            username = base64.b64encode(os.urandom(9)).decode()
            user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 给类视图的对象增加属性user，保存绑定用户对象
        self.context['view'].user = user

        # 保存QQ绑定的数据
        openid = validated_data['openid']
        OAuthQQUser.objects.create(
            user=user,
            openid=openid
        )

        # 由服务器生成一个jwt token，保存用户身份信息
        from rest_framework_jwt.settings import api_settings

        # 生成payload的方法
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        # 生成jwt token的方法
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 生成payload
        payload = jwt_payload_handler(user)
        # 生成jwt token
        token = jwt_encode_handler(payload)

        # 给user对象增加属性token，用来保存jwt token数据
        user.token = token

        return user
