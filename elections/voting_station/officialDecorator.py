from functools import wraps
from flask_jwt_extended import  verify_jwt_in_request, get_jwt
from flask import Response


def roleCheck (role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()

            if (("roles" in claims) and (role in claims["roles"])):
                return function(*arguments, **keywordArguments)
            else:
                return Response("permission denied", status=403)

        return decorator
    return innerRole