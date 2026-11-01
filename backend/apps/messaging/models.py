from django.conf import settings
from django.db import models


class Conversation(models.Model):
    class Kind(models.TextChoices):
        GROUP = "group", "Group chat"
        DIRECT = "direct", "Direct message"

    kind = models.CharField(max_length=8, choices=Kind.choices)
    batch = models.OneToOneField(
        "batches.Batch", null=True, blank=True, on_delete=models.CASCADE, related_name="group_chat"
    )
    title = models.CharField(max_length=120, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Participant", related_name="conversations")
    # Sorted key "minId:maxId" so each pair of users has a single DM thread.
    direct_key = models.CharField(max_length=40, unique=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return self.title or f"{self.kind} #{self.pk}"

    @classmethod
    def direct_between(cls, a, b):
        lo, hi = sorted([a.pk, b.pk])
        conv, created = cls.objects.get_or_create(direct_key=f"{lo}:{hi}", defaults={"kind": cls.Kind.DIRECT})
        if created:
            Participant.objects.bulk_create([Participant(conversation=conv, user=a), Participant(conversation=conv, user=b)])
        return conv

    @classmethod
    def group_for_batch(cls, batch):
        conv, _ = cls.objects.get_or_create(
            batch=batch, defaults={"kind": cls.Kind.GROUP, "title": batch.name}
        )
        return conv


class Participant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_read_id = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("conversation", "user")


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField(max_length=4000)
    artwork = models.ForeignKey("gallery.Artwork", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)
