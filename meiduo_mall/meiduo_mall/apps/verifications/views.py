import random

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from meiduo_mall.libs.yuntongxun.sms import CCP
from verifications.constants import SMS_CODE_EXPIRES, SEND_SMS_TEMP_ID, SMS_CODE_SEND

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
        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get("sms_send_%s" % mobile)

        if send_flag:
            return Response({"message": "发送短信验证码过于频繁"})

        # 1.随机生成六位验证码
        sms_code = "%06d" % random.randint(0, 999999)

        # 2.在Redis中存储短信验证码对象 k:sms_<mobile> v:sms_code

        pl = redis_conn.pipeline()
        # <key> <expires> <value>
        pl.setex("sms_%s" % mobile, SMS_CODE_EXPIRES, sms_code)
        pl.setex("sms_send_%s" % mobile, SMS_CODE_SEND, 1)

        pl.execute()

        # 3.使用云通讯给mobile发送消息
        expires = SMS_CODE_EXPIRES // 60

        from celery_tasks.sms.tasks import send_sms_code
        send_sms_code.delay(mobile, sms_code, expires)

        # 4.返回应答,短信发送结果
        return Response({'message': 'OK'})
