from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.gallery.models import Artwork

from .models import Order
from .serializers import OrderSerializer

S = Order.Status


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = Order.objects.filter(Q(buyer=u) | Q(seller=u)).select_related("artwork__artist", "artwork__batch",
                                                                          "buyer", "seller")
        role = self.request.query_params.get("role")
        if role == "buyer":
            qs = qs.filter(buyer=u)
        elif role == "seller":
            qs = qs.filter(seller=u)
        return qs

    def perform_create(self, serializer):
        art = serializer.validated_data["artwork"]
        serializer.save(buyer=self.request.user, seller=art.artist, amount_bdt=art.price_bdt)

    def _transition(self, order, allowed_from, to, actor):
        if actor == "seller" and order.seller_id != self.request.user.id:
            raise PermissionDenied("Only the artist can do this.")
        if actor == "either" and self.request.user.id not in (order.seller_id, order.buyer_id):
            raise PermissionDenied()
        if order.status not in allowed_from:
            return Response({"detail": f"Order is {order.get_status_display().lower()}."}, status=400)
        order.status = to
        order.save(update_fields=["status", "updated_at"])
        return None

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def accept(self, request, pk=None):
        order = self.get_object()
        if order.artwork.sale_status != Artwork.SaleStatus.AVAILABLE:
            return Response({"detail": "Artwork is no longer available."}, status=400)
        err = self._transition(order, [S.PENDING], S.ACCEPTED, "seller")
        if err:
            return err
        Artwork.objects.filter(pk=order.artwork_id).update(sale_status=Artwork.SaleStatus.RESERVED)
        # Other pending requests for the same artwork are declined automatically.
        Order.objects.filter(artwork=order.artwork, status=S.PENDING).exclude(pk=order.pk).update(status=S.REJECTED)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        order = self.get_object()
        return self._transition(order, [S.PENDING], S.REJECTED, "seller") or Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request, pk=None):
        order = self.get_object()
        err = self._transition(order, [S.ACCEPTED], S.COMPLETED, "seller")
        if err:
            return err
        Artwork.objects.filter(pk=order.artwork_id).update(sale_status=Artwork.SaleStatus.SOLD)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        was_accepted = order.status == S.ACCEPTED
        err = self._transition(order, [S.PENDING, S.ACCEPTED], S.CANCELLED, "either")
        if err:
            return err
        if was_accepted:
            Artwork.objects.filter(pk=order.artwork_id, sale_status=Artwork.SaleStatus.RESERVED).update(
                sale_status=Artwork.SaleStatus.AVAILABLE
            )
        return Response(self.get_serializer(order).data)
