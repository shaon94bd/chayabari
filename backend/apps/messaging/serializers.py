from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    artwork = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id", "sender", "body", "artwork", "created_at")

    def get_artwork(self, obj):
        a = obj.artwork
        if not a:
            return None
        return {"id": a.id, "title": a.title, "image": a.image.url if a.image else None}


class ConversationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    other = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "kind", "title", "other", "last_message", "unread", "updated_at")

    def _me(self):
        return self.context["request"].user

    def _other(self, obj):
        if obj.kind != Conversation.Kind.DIRECT:
            return None
        return next((m for m in obj.members.all() if m.id != self._me().id), None)

    def get_title(self, obj):
        if obj.kind == Conversation.Kind.GROUP:
            return obj.title or "Batch group"
        other = self._other(obj)
        return other.name if other else "Conversation"

    def get_other(self, obj):
        other = self._other(obj)
        return UserMiniSerializer(other).data if other else None

    def get_last_message(self, obj):
        m = obj.messages.select_related("sender").order_by("-id").first()
        if not m:
            return None
        return {"id": m.id, "body": m.body[:120], "sender": m.sender.name, "created_at": m.created_at}

    def get_unread(self, obj):
        p = obj.participants.filter(user=self._me()).first()
        last = p.last_read_id if p else 0
        return obj.messages.filter(id__gt=last).exclude(sender=self._me()).count()
