def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义响应方法
    """
    return {
        'user_id': user.id,
        'username': user.username,
        'token': token
    }