from celery_tasks.main import celery_app
from celery_tasks.sms.yuntongxun.sms import CCP

SEND_SMS_TEMP_ID = 1

import logging
logger = logging.getLogger('django')

@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code, expires):
    # expires = SMS_CODE_EXPIRES // 60
    try:
        res = CCP().send_template_sms("sms_%s" % mobile, [sms_code, expires], SEND_SMS_TEMP_ID)
    except Exception as e:
        logger.error('短信验证码发送异常:[mobile: %s sms_code: %s]' % (mobile, sms_code))
    else:
        if res != 0:
            logger.error('短信验证码发送失败:[mobile: %s sms_code: %s]' % (mobile, sms_code))
        else:
            logger.info('短信验证码发送成功:[mobile: %s sms_code: %s]' % (mobile, sms_code))
