from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from django.contrib.auth.models import update_last_login
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

from .models import User
from .serializers import (
    ArtistProfileSerializer,
    ChangePasswordSerializer,
    CollectorRegisterSerializer,
    MeSerializer,
)


def tokens_for(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"token": token.key}


def rotate_token(user):
    """Invalidate every existing session of this user (e.g. after a password change)."""
    Token.objects.filter(user=user).delete()
    return tokens_for(user)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        s = AuthTokenSerializer(data=request.data, context={"request": request})
        if not s.is_valid():
            return Response({"detail": "Wrong username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        user = s.validated_data["user"]
        update_last_login(None, user)
        return Response(tokens_for(user))


class LogoutView(APIView):
    """Log out everywhere: deletes the user's token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        user = request.user
        user.set_password(s.validated_data["new_password"])
        user.must_change_password = False
        user.save()
        return Response(rotate_token(user))


class CollectorRegisterView(generics.CreateAPIView):
    serializer_class = CollectorRegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response({**tokens_for(user), "user": MeSerializer(user).data}, status=status.HTTP_201_CREATED)


class ArtistProfileView(generics.RetrieveAPIView):
    serializer_class = ArtistProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        qs = User.objects.filter(is_active=True, batch__isnull=False).select_related("batch").annotate(
            artwork_count=Count("artworks", filter=Q(artworks__is_published=True))
        )
        return get_object_or_404(qs, username=self.kwargs["username"])
