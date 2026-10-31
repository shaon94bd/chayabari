from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.core.images import shrink_image_field


class Plan(models.Model):
    """A subscription plan sold to a batch (e.g. "Batch — 6 months")."""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    price_bdt = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField(default=180)
    max_members = models.PositiveIntegerField(default=40)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "price_bdt")

    def __str__(self):
        return f"{self.name} (৳{self.price_bdt})"


class Batch(models.Model):
    """A tenant: one year-batch of fine art students (e.g. JU Fine Art, 2021-22)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, max_length=60)
    institution = models.CharField(max_length=160)
    department = models.CharField(max_length=120, default="Fine Art")
    session = models.CharField(max_length=20, blank=True, help_text="e.g. 2021-22")
    about = models.TextField(blank=True)
    cover = models.ImageField(upload_to="batches/", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="owned_batches"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "batches"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        shrink_image_field(self.cover)
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name)[:50] or "batch"
        slug, i = base, 2
        while Batch.objects.filter(slug=slug).exists():
            slug, i = f"{base}-{i}", i + 1
        return slug

    # --- subscription helpers ---
    @property
    def current_subscription(self):
        now = timezone.now()
        return (
            self.subscriptions.filter(
                status__in=[Subscription.Status.ACTIVE, Subscription.Status.TRIAL],
                starts_at__lte=now,
                ends_at__gt=now,
            )
            .order_by("-ends_at")
            .first()
        )

    @property
    def is_active_subscription(self):
        if not hasattr(self, "_active_cache"):
            self._active_cache = self.current_subscription is not None
        return self._active_cache

    @property
    def max_members(self):
        sub = self.current_subscription
        if sub is None:
            return 0
        return sub.plan.max_members if sub.plan else settings.TRIAL_MAX_MEMBERS

    def start_trial(self):
        now = timezone.now()
        return Subscription.objects.create(
            batch=self,
            plan=None,
            status=Subscription.Status.TRIAL,
            starts_at=now,
            ends_at=now + timedelta(days=settings.TRIAL_DAYS),
        )


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "trial", "Free trial"
        PENDING = "pending", "Awaiting payment verification"
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.batch} · {self.plan or 'trial'} · {self.status}"

    @transaction.atomic
    def activate(self):
        """Activate after payment. Paid time stacks after any remaining active time."""
        now = timezone.now()
        latest_end = (
            Subscription.objects.filter(
                batch=self.batch, status=self.Status.ACTIVE, ends_at__gt=now
            )
            .exclude(pk=self.pk)
            .aggregate(m=models.Max("ends_at"))["m"]
        )
        start = latest_end or now
        self.status = self.Status.ACTIVE
        self.starts_at = start
        self.ends_at = start + timedelta(days=self.plan.duration_days)
        self.save()
        # A paid plan replaces the trial straight away.
        Subscription.objects.filter(batch=self.batch, status=self.Status.TRIAL).update(
            status=self.Status.CANCELLED
        )
        return self


class Payment(models.Model):
    """A manual mobile-banking payment (bKash / Nagad / Rocket) awaiting verification."""

    class Method(models.TextChoices):
        BKASH = "bkash", "bKash"
        NAGAD = "nagad", "Nagad"
        ROCKET = "rocket", "Rocket"
        BANK = "bank", "Bank transfer"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    subscription = models.OneToOneField(Subscription, on_delete=models.CASCADE, related_name="payment")
    amount_bdt = models.PositiveIntegerField()
    method = models.CharField(max_length=16, choices=Method.choices)
    transaction_id = models.CharField(max_length=64, unique=True)
    sender_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    note = models.CharField(max_length=255, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.method} {self.transaction_id} ({self.status})"

    @transaction.atomic
    def verify(self):
        if self.status == self.Status.VERIFIED:
            return
        self.status = self.Status.VERIFIED
        self.verified_at = timezone.now()
        self.save()
        self.subscription.activate()

    @transaction.atomic
    def reject(self, note=""):
        self.status = self.Status.REJECTED
        self.note = note or self.note
        self.save()
        self.subscription.status = Subscription.Status.CANCELLED
        self.subscription.save()
