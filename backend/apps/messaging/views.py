from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.gallery.models import Artwork

from .models import Conversation, Message, Participant
from .serializers import ConversationSerializer, MessageSerializer


def accessible_conversations(user):
    q = Q(participants__user=user)
    if user.batch_id:
        q |= Q(kind=Conversation.Kind.GROUP, batch_id=user.batch_id)
    return Conversation.objects.filter(q).distinct().prefetch_related("members")


def can_message(a, b):
    """Students message anyone; collectors may only message students (artists)."""
    if not b.is_active or a.pk == b.pk:
        return False
    if a.is_student:
        return True
    return b.is_student


class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.batch_id:
            group = Conversation.group_for_batch(user.batch)
            Participant.objects.get_or_create(conversation=group, user=user)
        convs = accessible_conversations(user).order_by("-updated_at")[:100]
        return Response(ConversationSerializer(convs, many=True, context={"request": request}).data)


class StartDirectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        other = get_object_or_404(User, pk=request.data.get("user_id"))
        if not can_message(request.user, other):
            return Response({"detail": "You can't message this user."}, status=403)
        conv = Conversation.direct_between(request.user, other)
        return Response(ConversationSerializer(conv, context={"request": request}).data, status=status.HTTP_201_CREATED)


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = 0
        for p in Participant.objects.filter(user=request.user).select_related("conversation"):
            total += p.conversation.messages.filter(id__gt=p.last_read_id).exclude(sender=request.user).count()
        return Response({"unread": total})


class MessageListCreateView(APIView):
    """GET ?after=<id> polls for new messages (oldest first); ?before=<id> pages history."""

    permission_classes = [permissions.IsAuthenticated]

    def get_conversation(self, request, pk):
        return get_object_or_404(accessible_conversations(request.user), pk=pk)

    def get(self, request, pk):
        conv = self.get_conversation(request, pk)
        qs = conv.messages.select_related("sender", "artwork")
        after, before = request.query_params.get("after"), request.query_params.get("before")
        if after:
            msgs = list(qs.filter(id__gt=int(after))[:200])
        else:
            if before:
                qs = qs.filter(id__lt=int(before))
            msgs = list(qs.order_by("-id")[:50])[::-1]
        if msgs:
            p, _ = Participant.objects.get_or_create(conversation=conv, user=request.user)
            if msgs[-1].id > p.last_read_id:
                p.last_read_id = msgs[-1].id
                p.save(update_fields=["last_read_id"])
        return Response(MessageSerializer(msgs, many=True).data)

    def post(self, request, pk):
        conv = self.get_conversation(request, pk)
        body = (request.data.get("body") or "").strip()
        if not body:
            return Response({"body": ["Message can't be empty."]}, status=400)
        if len(body) > 4000:
            return Response({"body": ["Message is too long."]}, status=400)
        if conv.kind == Conversation.Kind.GROUP and not request.user.batch.is_active_subscription:
            return Response({"detail": "Your subscription is not active."}, status=402)
        artwork = None
        if request.data.get("artwork_id"):
            artwork = Artwork.objects.filter(pk=request.data["artwork_id"]).first()
        msg = Message.objects.create(conversation=conv, sender=request.user, body=body, artwork=artwork)
        conv.save(update_fields=["updated_at"])
        Participant.objects.update_or_create(
            conversation=conv, user=request.user, defaults={"last_read_id": msg.id}
        )
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
