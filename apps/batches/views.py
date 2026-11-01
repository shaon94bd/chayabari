from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import MeSerializer
from apps.accounts.utils import generate_password
from apps.accounts.views import rotate_token, tokens_for
from apps.core.permissions import IsBatchMember, IsBatchOwner

from .models import Batch, Plan
from .serializers import (
    BatchSerializer,
    CheckoutSerializer,
    CredentialSerializer,
    MemberSerializer,
    NewMemberSerializer,
    PlanSerializer,
    SignupSerializer,
    SubscriptionSerializer,
    create_members,
)


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        s = SignupSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        owner = s.save()
        return Response({**tokens_for(owner), "user": MeSerializer(owner).data}, status=status.HTTP_201_CREATED)


class MyBatchView(generics.RetrieveUpdateAPIView):
    serializer_class = BatchSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [IsBatchMember()]
        return [IsBatchOwner()]

    def get_object(self):
        return self.request.user.batch


class MemberListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsBatchMember()]
        return [IsBatchOwner()]

    def get(self, request):
        qs = request.user.batch.members.order_by("-role", "display_name", "username")
        if request.user.role != User.Role.OWNER:
            qs = qs.filter(is_active=True)
        return Response(MemberSerializer(qs, many=True).data)

    def post(self, request):
        """Add one member ({display_name, username?, phone?}) or many ({members: [...]})."""
        many = "members" in request.data
        rows = request.data["members"] if many else [request.data]
        s = NewMemberSerializer(data=rows, many=True)
        s.is_valid(raise_exception=True)
        if not request.user.batch.is_active_subscription:
            return Response({"detail": "Your subscription is not active."}, status=status.HTTP_402_PAYMENT_REQUIRED)
        created = create_members(request.user.batch, s.validated_data)
        return Response({"credentials": CredentialSerializer(created, many=True).data}, status=status.HTTP_201_CREATED)


class MemberDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = MemberSerializer
    permission_classes = [IsBatchOwner]

    def get_queryset(self):
        return self.request.user.batch.members.exclude(pk=self.request.user.pk)

    def perform_update(self, serializer):
        if serializer.validated_data.get("is_active") and not serializer.instance.is_active:
            from .serializers import check_seats

            check_seats(self.request.user.batch, 1)
        serializer.save()


class MemberResetPasswordView(APIView):
    permission_classes = [IsBatchOwner]

    def post(self, request, pk):
        member = get_object_or_404(request.user.batch.members.exclude(pk=request.user.pk), pk=pk)
        password = generate_password()
        member.set_password(password)
        member.must_change_password = True
        member.save()
        rotate_token(member)  # logs the member out of any device using the old password
        return Response(CredentialSerializer((member, password)).data)


class TransferOwnershipView(APIView):
    """Hand the batch to another member (e.g. the owner graduates or leaves)."""

    permission_classes = [IsBatchOwner]

    def post(self, request, pk):
        batch = request.user.batch
        new_owner = get_object_or_404(batch.members.filter(is_active=True).exclude(pk=request.user.pk), pk=pk)
        new_owner.role = User.Role.OWNER
        new_owner.save(update_fields=["role"])
        request.user.role = User.Role.MEMBER
        request.user.save(update_fields=["role"])
        batch.owner = new_owner
        batch.save(update_fields=["owner"])
        return Response({"detail": f"{new_owner.name} is now the batch owner."})


class SubscriptionView(APIView):
    permission_classes = [IsBatchMember]

    def get(self, request):
        batch = request.user.batch
        current = batch.current_subscription
        return Response({
            "is_active": current is not None,
            "current": SubscriptionSerializer(current).data if current else None,
            "history": SubscriptionSerializer(batch.subscriptions.select_related("plan", "payment"), many=True).data,
            "seats_used": batch.members.filter(is_active=True).count(),
            "seats_total": batch.max_members,
            "payment_numbers": settings.PAYMENT_INSTRUCTIONS,
        })


class CheckoutView(APIView):
    permission_classes = [IsBatchOwner]

    def post(self, request):
        s = CheckoutSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        sub = s.save()
        return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


class PublicBatchView(APIView):
    """Public showcase page for a batch: /b/<slug>."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        batch = get_object_or_404(Batch, slug=slug)
        if not batch.is_active_subscription:
            return Response({"detail": "This batch's page is currently unavailable."}, status=status.HTTP_404_NOT_FOUND)
        members = batch.members.filter(is_active=True).annotate(
            artwork_count=Count("artworks", filter=Q(artworks__is_published=True))
        ).order_by("display_name", "username")
        return Response({
            **BatchSerializer(batch).data,
            "artists": [
                {"id": m.id, "username": m.username, "name": m.name,
                 "avatar": m.avatar.url if m.avatar else None, "artwork_count": m.artwork_count}
                for m in members
            ],
        })
