from django.contrib import admin

from .models import Conversation, Message, Participant


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "title", "batch", "updated_at")
    inlines = [ParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
