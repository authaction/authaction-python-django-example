from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.authentication import AuthActionAuthentication


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def public_view(request: Request) -> Response:
    return Response({"message": "This is a public message!"})


@api_view(["GET"])
@authentication_classes([AuthActionAuthentication])
@permission_classes([IsAuthenticated])
def protected_view(request: Request) -> Response:
    return Response({
        "message": "This is a protected message!",
        "sub": request.user.sub,
    })
