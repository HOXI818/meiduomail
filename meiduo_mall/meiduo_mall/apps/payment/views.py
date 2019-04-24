import os

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.conf import settings

from orders.models import OrderInfo
from payment.models import Payment

from alipay import AliPay
# Create your views here.

# /pay_success.html?
# charset=utf-8&
# out_trade_no=201902211050400000000002& # 商户订单号
# method=alipay.trade.page.pay.return&
# total_amount=3398.00&
# 签名字符串
# sign=Pv6rTtfkNck4JnudabAKsn9XrfVeIm9fQE6%2FU1IENkn8hD43JQLlYDBG7FFAiek41LVwDQ6qrAyTyMinYJ4l5Twt1SF4VcDJ%2BPvgPSwBvtQe5THtZA1LBW%2FzbuF3dbZsokbrZ8K86wP6fNMdckxZfRmFG67EMm1GoeY59u5fQ4Kt4N82hvmdaRWdHykhLqGgo%2FyxQEyKUq7iqCE%2BKM0Co%2FGcP6B8k6iRObjsYJ0S5yKFoTFwPg6f99v2OREUqg1%2F8AmuHK1KSk1TsHBngSB75ItwRlCC1gPcQ8%2BC8gEzR94%2BPgCaVW274yllv%2BbwfWqWeqT8DKoVUk5LIHEx1rKiDg%3D%3D&
# trade_no=2019022122001485920500708358& # 支付交易号
# auth_app_id=2016090800464054&
# version=1.0&
# app_id=2016090800464054&
# sign_type=RSA2&
# seller_id=2088102174694091&
# timestamp=2019-02-21+10%3A58%3A10


# PUT /payment/status/?<支付结果数据>
class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        保存支付结果:
        1. 获取支付结果数据并进行签名验证
        2. 校验订单是否有效
        3. 保存支付结果并修改订单支付状态
        4. 返回支付交易编号
        """
        # 1. 获取支付结果数据并进行签名验证
        data = request.query_params.dict() # QueryDict->dict

        signature = data.pop('sign')

        # 签名验证
        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,  # 开发者应用APPID
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, "apps/payment/keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, "apps/payment/keys/alipay_public_key.pem"),
            sign_type="RSA2",  # 签名算法
            debug=settings.ALIPAY_DEBUG  # 默认False，是否使用沙箱环境
        )

        success = alipay.verify(data, signature)

        if not success:
            # 签名验证失败
            return Response({'message': '非法操作'}, status=status.HTTP_403_FORBIDDEN)

        # 2. 校验订单是否有效
        order_id = data.get('out_trade_no')
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=request.user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'],  # 支付宝支付
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']  # 待支付
                                          )
        except OrderInfo.DoesNotExist:
            return Response({'message': '无效的order_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 保存支付结果并修改订单支付状态
        trade_id = data.get('trade_no')
        Payment.objects.create(
            order=order,
            trade_id=trade_id
        )

        # 修改订单支付状态
        order.status = OrderInfo.ORDER_STATUS_ENUM['UNSEND'] # 待发货
        order.save()

        # 4. 返回支付交易编号
        return Response({'trade_id': trade_id})


# GET /orders/(?P<order_id>\d+)/payment/
class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        获取支付宝支付网址和参数:
        1. 获取order_id并校验订单是否有效
        2. 组织支付宝支付网址和参数
        3. 返回支付宝支付网址和参数
        """
        # 获取登录用户
        user = request.user

        # 1. 获取order_id并校验订单是否有效
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'], # 支付宝支付
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] # 待支付
                                          )
        except OrderInfo.DoesNotExist:
            return Response({'message': '无效的order_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 组织支付宝支付网址和参数
        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APPID, # 开发者应用APPID
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, "apps/payment/keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(settings.BASE_DIR,"apps/payment/keys/alipay_public_key.pem"),
            sign_type="RSA2",  # 签名算法
            debug=settings.ALIPAY_DEBUG # 默认False，是否使用沙箱环境
        )

        # 组织支付参数
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_amount # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 商户订单号
            total_amount=str(total_pay), # 订单总金额
            subject='美多商城%s' % order_id, # 订单标题
            return_url="http://www.meiduo.site:8080/pay_success.html", # 回调地址
        )

        # 3. 返回支付宝支付网址和参数
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return Response({"alipay_url": alipay_url})