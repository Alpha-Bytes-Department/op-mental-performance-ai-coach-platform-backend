from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'error': {
                'message': ''
            },
            'status': response.status_code
        }

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response['error']['message'] = response.data['detail']
            elif 'non_field_errors' in response.data:
                custom_response['error']['message'] = response.data['non_field_errors'][0]
            else:
                # For other validation errors, we can concatenate the error messages
                errors = []
                for key, value in response.data.items():
                    errors.append(f"{key}: {', '.join(value)}")
                custom_response['error']['message'] = ', '.join(errors)
        else:
            custom_response['error']['message'] = str(response.data)

        response.data = custom_response

    return response
