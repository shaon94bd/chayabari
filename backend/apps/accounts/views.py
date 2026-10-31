from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    ArtistProfileSerializer,
    ChangePasswordSerializer,
    CollectorRegisterSerializer,
    MeSerializer,
)


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


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
        return Response(tokens_for(user))


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
