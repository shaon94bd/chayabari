from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import HasActiveSubscription, active_batch_q

from .models import Artwork, ArtworkImage, Exhibition
from .serializers import (
    ArtworkImageSerializer,
    ArtworkListSerializer,
    ArtworkSerializer,
    ArtworkWriteSerializer,
    ExhibitionDetailSerializer,
    ExhibitionSerializer,
)


class ArtworkViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [HasActiveSubscription()]

    def get_serializer_class(self):
        if self.action == "list":
            return ArtworkListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ArtworkWriteSerializer
        return ArtworkSerializer

    def get_queryset(self):
        user = self.request.user
        visible = Q(is_published=True) & active_batch_q()
        if user.is_authenticated:
            visible |= Q(artist=user)
        qs = Artwork.objects.filter(visible).select_related("artist", "batch").distinct()
        p = self.request.query_params
        if p.get("mine") and user.is_authenticated:
            qs = qs.filter(artist=user)
        if p.get("batch"):
            qs = qs.filter(batch__slug=p["batch"])
        if p.get("artist"):
            qs = qs.filter(artist__username=p["artist"])
        if p.get("for_sale"):
            qs = qs.filter(sale_status=Artwork.SaleStatus.AVAILABLE)
        if p.get("q"):
            q = p["q"]
            qs = qs.filter(Q(title__icontains=q) | Q(medium__icontains=q) | Q(artist__display_name__icontains=q))
        return qs

    def _check_owner(self, artwork):
        if artwork.artist_id != self.request.user.id:
            raise PermissionDenied("Only the artist can change this artwork.")

    def perform_create(self, serializer):
        serializer.save(artist=self.request.user, batch=self.request.user.batch)

    def perform_update(self, serializer):
        self._check_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_owner(instance)
        if instance.sale_status == Artwork.SaleStatus.SOLD:
            raise PermissionDenied("Sold artworks are kept for the record. Unpublish it instead.")
        instance.delete()

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        self.perform_create(s)
        return Response(ArtworkSerializer(s.instance, context=self.get_serializer_context()).data, status=201)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(ArtworkSerializer(self.get_object(), context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="images")
    def add_image(self, request, pk=None):
        artwork = self.get_object()
        self._check_owner(artwork)
        if artwork.extra_images.count() >= 6:
            return Response({"detail": "Up to 6 extra photos per artwork."}, status=400)
        s = ArtworkImageSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(artwork=artwork, order=artwork.extra_images.count())
        return Response(s.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>\d+)")
    def remove_image(self, request, pk=None, image_id=None):
        artwork = self.get_object()
        self._check_owner(artwork)
        ArtworkImage.objects.filter(artwork=artwork, pk=image_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExhibitionViewSet(viewsets.ModelViewSet):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [HasActiveSubscription()]

    def get_serializer_class(self):
        return ExhibitionSerializer if self.action == "list" else ExhibitionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        visible = Q(is_published=True) & active_batch_q()
        if user.is_authenticated and user.batch_id:
            visible |= Q(batch_id=user.batch_id)
        qs = Exhibition.objects.filter(visible).select_related("batch", "created_by").distinct()
        p = self.request.query_params
        if p.get("batch"):
            qs = qs.filter(batch__slug=p["batch"])
        if p.get("mine_batch") and user.is_authenticated:
            qs = qs.filter(batch_id=user.batch_id)
        return qs

    def _check_editor(self, exhibition):
        u = self.request.user
        if exhibition.batch_id != u.batch_id or (exhibition.created_by_id != u.id and u.role != "owner"):
            raise PermissionDenied("Only the curator or group owner can change this exhibition.")

    def perform_create(self, serializer):
        serializer.save(batch=self.request.user.batch, created_by=self.request.user)

    def perform_update(self, serializer):
        self._check_editor(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_editor(instance)
        instance.delete()
