from rest_framework.permissions import BasePermission


class IsBatchMember(BasePermission):
    """Student (owner or member) belonging to a batch."""

    message = "Only group members can do this."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.batch_id)


class HasActiveSubscription(BasePermission):
    """The user's batch must have an active (trial or paid) subscription."""

    message = "Your subscription is not active. Ask your group owner to renew."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.batch_id and u.batch.is_active_subscription)


class IsBatchOwner(BasePermission):
    message = "Only the group owner can do this."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.batch_id and u.role == "owner")


def active_batch_q(prefix="batch__"):
    """Q filter: rows whose batch currently has a trial/active subscription."""
    from django.db.models import Q
    from django.utils import timezone

    now = timezone.now()
    return Q(**{
        f"{prefix}subscriptions__status__in": ["trial", "active"],
        f"{prefix}subscriptions__starts_at__lte": now,
        f"{prefix}subscriptions__ends_at__gt": now,
    })
