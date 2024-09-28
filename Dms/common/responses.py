

def get_success_response(data):
    response = {
        'status_code': 200,
        'message': 'Request successful',
        'data': data,
        'error': False        
    }

    return response


def get_error_response():
    response = {
        'status_code': 400,
        'message': 'Request successful',
        'data': {},
        'error': True       
    }
    return response