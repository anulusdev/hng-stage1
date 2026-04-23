from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Overrides DRF's default exception handler to return responses
    in the task's required format:
    {"status": "error", "message": "<description>"}

    Called automatically by DRF whenever an exception is raised.
    We only need to register it in settings.py once.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        errors = exc.detail

        if isinstance(errors, dict):
            first_field = next(iter(errors))
            first_message = errors[first_field]
            if isinstance(first_message, list):
                first_message = str(first_message[0])
            else:
                first_message = str(first_message)

            if 'numbers' in first_message.lower() or 'valid string' in first_message.lower():
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                status_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(errors, list):
            first_message = str(errors[0])
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            first_message = str(errors)
            status_code = status.HTTP_400_BAD_REQUEST

        return Response(
            {'status': 'error', 'message': first_message},
            status=status_code
        )

    if response is not None:
        message = str(exc)
        return Response(
            {'status': 'error', 'message': message},
            status=response.status_code
        )

    return response