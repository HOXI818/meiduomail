import random

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from meiduo_mall.libs.yuntongxun.sms import CCP
from verifications.constants import SMS_CODE_EXPIRES, SEND_SMS_TEMP_ID

import logging
logger = logging.getLogger('django')

class SMSCodeView(APIView):
    def get(self, request, mobile):
        """
        获取短信验证码
        1.随机生成六位验证码
        2.在Redis中存储短信验证码对象 k:sms_<mobile> v:sms_code
        3.时运云通讯给mobile发送消息
        4.返回应答,短信发送结果
        """
        # 1.随机生成六位验证码
        sms_code = "%06d" % random.randint(0, 999999)

        # 2.在Redis中存储短信验证码对象 k:sms_<mobile> v:sms_code
        redis_conn = get_redis_connection('verify_codes')

        # <key> <expires> <value>
        redis_conn.setex("sms_%s" % mobile, SMS_CODE_EXPIRES, sms_code)

        # 3.使用云通讯给mobile发送消息
        expires = SMS_CODE_EXPIRES // 60
        try:
            res = CCP().send_template_sms("sms_%s" % mobile, [sms_code, expires], SEND_SMS_TEMP_ID)
        except Exception as e:
            logger.error(e)
            return Response({'message':'验证码发送异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if res != 0:
            return Response({'message':"验证码发送失败"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 4.返回应答,短信发送结果
        return Response({'message': 'OK'})
