from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.permissions import HasActiveSubscription, active_batch_q

from .models import Auction
from .serializers import AuctionSerializer, BidSerializer


class AuctionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AuctionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "bids"):
            return [permissions.AllowAny()]
        if self.action == "bid":
            return [permissions.IsAuthenticated()]
        return [HasActiveSubscription()]

    def get_queryset(self):
        user = self.request.user
        visible = Q(is_cancelled=False) & active_batch_q()
        if user.is_authenticated and user.batch_id:
            visible |= Q(batch_id=user.batch_id)
        qs = Auction.objects.filter(visible).select_related("artwork__artist", "artwork__batch").distinct()
        p = self.request.query_params
        now = timezone.now()
        phase = p.get("phase")
        if phase == "live":
            qs = qs.filter(is_cancelled=False, starts_at__lte=now, ends_at__gt=now)
        elif phase == "scheduled":
            qs = qs.filter(is_cancelled=False, starts_at__gt=now)
        elif phase == "ended":
            qs = qs.filter(ends_at__lte=now)
        elif phase == "open":
            qs = qs.filter(is_cancelled=False, ends_at__gt=now).order_by("ends_at")
        if p.get("batch"):
            qs = qs.filter(batch__slug=p["batch"])
        if p.get("mine") and user.is_authenticated:
            qs = qs.filter(Q(artwork__artist=user) | Q(bids__bidder=user)).distinct()
        return qs

    def _settle_ended(self, auctions):
        for a in auctions:
            if not a.is_settled and a.phase == "ended":
                a.settle()

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        self._settle_ended(page)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        auction = self.get_object()
        self._settle_ended([auction])
        return Response(self.get_serializer(auction).data)

    def perform_create(self, serializer):
        artwork = serializer.validated_data["artwork"]
        serializer.save(created_by=self.request.user, batch=artwork.batch)

    @action(detail=True, methods=["get"])
    def bids(self, request, pk=None):
        auction = self.get_object()
        return Response(BidSerializer(auction.bids.select_related("bidder")[:50], many=True).data)

    @action(detail=True, methods=["post"])
    def bid(self, request, pk=None):
        auction = self.get_object()
        try:
            amount = int(request.data.get("amount"))
        except (TypeError, ValueError):
            return Response({"amount": ["Enter a whole number of taka."]}, status=400)
        try:
            bid = auction.place_bid(request.user, amount)
        except DjangoValidationError as e:
            return Response({"detail": e.messages[0]}, status=400)
        return Response(
            {"bid": BidSerializer(bid).data, "auction": self.get_serializer(auction).data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        auction = self.get_object()
        if auction.artwork.artist_id != request.user.id and not (
            request.user.role == "owner" and auction.batch_id == request.user.batch_id
        ):
            raise PermissionDenied("Only the artist or group owner can cancel.")
        if auction.bids.exists():
            return Response({"detail": "Auctions with bids cannot be cancelled."}, status=400)
        auction.is_cancelled = True
        auction.save(update_fields=["is_cancelled"])
        return Response(self.get_serializer(auction).data)
