from django.conf import settings
from django.contrib.auth import password_validation
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.utils import generate_password, unique_username
from apps.core.fields import AbsoluteImageField

from .models import Batch, Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "code", "name", "description", "price_bdt", "duration_days", "max_members")


class BatchSerializer(serializers.ModelSerializer):
    cover = AbsoluteImageField(required=False, allow_null=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = ("id", "name", "slug", "institution", "department", "session", "about", "cover", "member_count")
        read_only_fields = ("slug",)

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()


class SignupSerializer(serializers.Serializer):
    """A student creates their batch and becomes its owner (starts a free trial)."""

    # owner
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(max_length=120)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    # batch
    batch_name = serializers.CharField(max_length=120)
    institution = serializers.CharField(max_length=160)
    department = serializers.CharField(max_length=120, required=False, default="Fine Art")
    session = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate(self, attrs):
        password_validation.validate_password(attrs["password"], User(username=attrs["username"]))
        return attrs

    @transaction.atomic
    def create(self, v):
        from apps.messaging.models import Conversation

        batch = Batch.objects.create(
            name=v["batch_name"], institution=v["institution"],
            department=v.get("department") or "Fine Art", session=v.get("session", ""),
        )
        owner = User(
            username=v["username"], display_name=v["display_name"], email=v.get("email", ""),
            phone=v.get("phone", ""), role=User.Role.OWNER, batch=batch,
        )
        owner.set_password(v["password"])
        owner.save()
        batch.owner = owner
        batch.save(update_fields=["owner"])
        batch.start_trial()
        Conversation.group_for_batch(batch)
        return owner


class MemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    avatar = AbsoluteImageField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "name", "display_name", "phone", "email", "avatar", "role",
                  "is_active", "must_change_password", "last_login", "date_joined")
        read_only_fields = ("username", "role", "must_change_password", "last_login", "date_joined", "avatar")


class NewMemberSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=120)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if value and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(f"Username '{value}' is taken.")
        return value


def check_seats(batch, adding):
    limit = batch.max_members
    used = batch.members.filter(is_active=True).count()
    if used + adding > limit:
        raise serializers.ValidationError(
            {"detail": f"Your plan allows {limit} members; you have {used}. Upgrade to add more."}
        )


@transaction.atomic
def create_members(batch, rows):
    """Create member accounts; returns (user, plain_password) pairs. Passwords are shown once."""
    check_seats(batch, len(rows))
    seen = set()
    created = []
    for row in rows:
        username = row.get("username") or unique_username(row["display_name"], User)
        if username.lower() in seen:
            raise serializers.ValidationError({"detail": f"Duplicate username '{username}' in list."})
        seen.add(username.lower())
        password = generate_password()
        user = User(
            username=username, display_name=row["display_name"], phone=row.get("phone", ""),
            role=User.Role.MEMBER, batch=batch, must_change_password=True,
        )
        user.set_password(password)
        user.save()
        created.append((user, password))
    return created


class CredentialSerializer(serializers.Serializer):
    def to_representation(self, pair):
        user, password = pair
        return {"id": user.id, "name": user.name, "username": user.username, "password": password}


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ("id", "plan", "status", "starts_at", "ends_at", "created_at", "payment")

    def get_payment(self, obj):
        p = getattr(obj, "payment", None)
        if not p:
            return None
        return {"method": p.method, "transaction_id": p.transaction_id, "amount_bdt": p.amount_bdt,
                "status": p.status, "note": p.note, "created_at": p.created_at}


class CheckoutSerializer(serializers.Serializer):
    plan = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(is_active=True))
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    transaction_id = serializers.CharField(max_length=64)
    sender_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_transaction_id(self, value):
        value = value.strip().upper()
        if Payment.objects.filter(transaction_id=value).exists():
            raise serializers.ValidationError("This transaction ID was already submitted.")
        return value

    @transaction.atomic
    def create(self, v):
        request = self.context["request"]
        batch = request.user.batch
        if batch.subscriptions.filter(status=Subscription.Status.PENDING).exists():
            raise serializers.ValidationError({"detail": "A payment is already awaiting verification."})
        sub = Subscription.objects.create(batch=batch, plan=v["plan"], status=Subscription.Status.PENDING)
        payment = Payment.objects.create(
            subscription=sub, amount_bdt=v["plan"].price_bdt, method=v["method"],
            transaction_id=v["transaction_id"], sender_number=v.get("sender_number", ""),
            submitted_by=request.user,
        )
        if settings.PAYMENT_AUTO_VERIFY:
            payment.verify()
            sub.refresh_from_db()
        return sub
