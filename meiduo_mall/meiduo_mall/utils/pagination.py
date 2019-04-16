from rest_framework.pagination import PageNumberPagination


class StandardResultPagination(PageNumberPagination):
    """自定义分页类"""
    # 分页默认`页容量`
    page_size = 6
    # 获取分页数据时，传递`页容量`参数名称
    page_size_query_param = 'page_size'
    # 最大`页容量`
    max_page_size = 20
