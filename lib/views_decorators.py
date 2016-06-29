from rest_framework import exceptions
from webservice.models import Token

from functools import wraps


def expect_username(view_func):
    """Check that the user has provided a username.
    """

    def wrapped_view(*args, **kwargs):
        if len(args) < 1:
            raise Exception("No request was provided :(")
        request = args[0]
        username = None
        # check if api_token is included in URL
        if "username" in request.query_params:
            username = str(request.query_params["username"])
        # check if api_token in included in request's META field
        if "HTTP_USERNAME" in request.META:
            username = request.META.get('HTTP_USERNAME')
        if username is None:
            raise exceptions.AuthenticationFailed('No USER has been provided')
        # Set an "api_token" field to ease its usage by view methods
        request.username = username
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def expect_apitoken(view_func):
    """Check that the user has provided an api token.
    """

    def wrapped_view(*args, **kwargs):
        if len(args) < 1:
            raise Exception("No request was provided :(")
        request = args[0]
        token = None
        # check if api_token is included in URL
        if "token" in request.query_params:
            token = str(request.query_params["token"])
        # check if api_token in included in request's META field
        if "HTTP_TOKEN" in request.META:
            token = request.META.get('HTTP_TOKEN')
        if token is None:
            raise exceptions.AuthenticationFailed('No TOKEN has been provided')
        # Set an "api_token" field to ease its usage by view methods
        request.token = token
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def expect_password(view_func):
    """Check that the user has provided a password.
    """

    def wrapped_view(*args, **kwargs):
        if len(args) < 1:
            raise Exception("No request was provided :(")
        request = args[0]
        password = None
        # check if api_token is included in URL
        if "password" in request.query_params:
            password = str(request.query_params["password"])
        # check if api_token in included in request's META field
        if "HTTP_PASSWORD" in request.META:
            password = request.META.get('HTTP_PASSWORD')
        if password is None:
            raise exceptions.AuthenticationFailed('No PASSWORD has been provided')
        # Set an "api_token" field to ease its usage by view methods
        request.password = password
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def token_authentication(view_func):
    """Check that a valid token has been provided.
    """

    def wrapped_view(*args, **kwargs):
        if len(args) < 1:
            raise Exception("No request was provided :(")
        request = args[0]
        if not hasattr(request, "token"):
            raise exceptions.AuthenticationFailed('no token has been provided :(')
        token = request.token
        tokens = Token.objects.filter(token=token).all()
        if len(tokens) == 0:
            raise exceptions.AuthenticationFailed('token not valid :(')
        request.username = tokens[0].username
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def user_authentication(view_func):
    """Check that a valid user has been provided.
    """

    def wrapped_view(*args, **kwargs):
        if len(args) < 1:
            raise Exception("No request was provided :(")
        request = args[0]
        if not hasattr(request, "username") or not hasattr(request, "password"):
            raise exceptions.AuthenticationFailed('need a username and a password :(')
        username = request.username
        password = request.password
        from django.contrib.auth.models import User
        users = User.objects.filter(username=username).all()
        if len(users) == 0:
            raise exceptions.AuthenticationFailed('user not valid :(')
        user = User.objects.filter(username=username).first()
        if not user.check_password(password):
            raise exceptions.AuthenticationFailed('user not valid :(')
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)
