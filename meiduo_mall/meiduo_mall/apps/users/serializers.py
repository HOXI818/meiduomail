import re
from django_redis import get_redis_connection
from rest_framework import serializers

from users.models import User, Address


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器类"""
    password2 = serializers.CharField(label='重复密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='JWT token', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'mobile', 'password2', 'sms_code', 'allow', 'token')

        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的密码',
                    'max_length': '仅允许5-20个字符的密码',
                }
            }
        }

    # 是否同意协议, 手机号格式, 手机号是否存在, 两次密码是否一致, 短信验证码是否正确
    def validate_username(self, value):
        # 用户名不能全为数字
        if re.match('^\d+$', value):
            raise serializers.ValidationError('用户名不能全为数字')
        return value

    def validate_allow(self, value):
        # 是否同意协议
        if value != 'true':
            raise serializers.ValidationError('请同意协议')

        return value

    def validate_mobile(self, value):
        # 手机号格式
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')

        # 手机号是否已存在
        count = User.objects.filter(mobile=value).count()

        if count > 0:
            raise serializers.ValidationError('手机号已存在')

        return value

    def validate(self, attrs):
        # 两次密码是否一致
        password = attrs['password']
        password2 = attrs['password2']

        if password != password2:
            raise serializers.ValidationError('两次密码不一致')

        # 短信验证码是否正确
        mobile = attrs['mobile']

        redis_conn = get_redis_connection('verify_codes')

        real_sms_code = redis_conn.get("sms_%s" % mobile)  # byte

        if real_sms_code is None:
            raise serializers.ValidationError('短信验证码已失效')

        sms_code = attrs['sms_code']  # str

        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('短信验证码错误')

        return attrs

    def create(self, validated_data):
        """validate_data: 校验之后的数据"""
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        user = User.objects.create_user(**validated_data)

        # 生成 jwt token
        from rest_framework_jwt.settings import api_settings

        # 生成payload的方法
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        # 生成jwt token的方法
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 生成payload
        payload = jwt_payload_handler(user)
        # 生成jwt token
        token = jwt_encode_handler(payload)

        # 给user添加token属性，保存jwt token
        user.token = token

        return user


class UserDetialSerializer(serializers.ModelSerializer):
    """用户序列化器类"""
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    """邮箱设置序列化器类"""
    class Meta:
        model = User
        fields = ('id', 'email')

        extra_kwargs = {
            'email': {
                'required': True
            }
        }


     # 设置邮箱并给邮箱发送验证邮件
    def update(self, instance, validated_data):
        email = validated_data['email']
        instance.email = email
        instance.save()

        # 给邮箱发送验证邮件
        verify_url = instance.generate_verify_email_url()

        # 发出发送邮件任务的消息
        from celery_tasks.email.tasks import send_verify_email
        send_verify_email.delay(email, verify_url)

        return instance


class AddressSerializer(serializers.ModelSerializer):
    """地址序列化器类"""
    # 增加模型类中没有的字段
    province_id = serializers.IntegerField(label='省id')
    city_id = serializers.IntegerField(label='市id')
    district_id = serializers.IntegerField(label='区县id')
    # 重写字段，只需要名字
    province = serializers.StringRelatedField(label='省', read_only=True)
    city = serializers.StringRelatedField(label='市', read_only=True)
    district = serializers.StringRelatedField(label='区县', read_only=True)
    class Meta:
        model = Address
        # 排除不需要的字段
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        # 手机号格式
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')

        return value

    def create(self, validated_data):
        # 创建并保存新增地址数据

        # 获取用户登录对象,需要context获取user对象
        user = self.context['request'].user
        validated_data['user'] = user

        # 调用ModelSerializer中create方法
        addr = super().create(validated_data)
        return addr


















