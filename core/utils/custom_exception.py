from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if response.data.get('message'):
            del response.data['message']

        if response.data.get('success') is None:
            response.data['success'] = False

    return response