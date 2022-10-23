"""
Custom authentication class for Django Rest Framework.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django_keycloak import Token


class KeycloakAuthentication(BaseAuthentication):
    """
    All authentication classes should extend BaseAuthentication.
    """

    authenticate_header = "Bearer"

    @staticmethod
    def get_authorization_header(request):
        """
        Return request's 'Authorization:' header, as a bytestring.
        Hide some test client ickyness where the header can be unicode.
        """
        auth = request.META.get("HTTP_AUTHORIZATION", b"")
        if isinstance(auth, str):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth

    @staticmethod
    def get_token(request):
        """Get the token from the HTTP request"""
        auth_header = request.META.get("HTTP_AUTHORIZATION").split()
        if len(auth_header) == 2:
            return auth_header[1]
        return None

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = self.get_authorization_header(request)

        # If request does not contain an authorization header, return
        # an anonymous user
        if not auth_header:
            return AnonymousUser(), None

        # Otherwise try to create a "Token" object from the request token
        token = Token.from_access_token(self.get_token(request))
        # If token is None it is not valid, immediately return error
        # avoid the database query
        if not token:
            raise AuthenticationFailed

        # Get the associated user by keycloak id
        user = get_user_model().objects.get_by_keycloak_id(token.user_id)

        # Return the user and the associated access token
        return user, token.access_token

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return self.authenticate_header
