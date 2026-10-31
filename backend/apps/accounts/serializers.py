from django.contrib.auth import password_validation
from rest_framework import serializers

from apps.core.fields import AbsoluteImageField

from .models import User


class UserMiniSerializer(serializers.ModelSerializer):
    """Public-safe representation used inside other objects."""

    name = serializers.CharField(read_only=True)
    avatar = AbsoluteImageField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "name", "avatar", "role")


class BatchMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    institution = serializers.CharField()
    session = serializers.CharField()


class MeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    avatar = AbsoluteImageField(required=False, allow_null=True)
    batch = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "name", "display_name", "first_name", "last_name", "email", "phone",
            "bio", "avatar", "role", "batch", "must_change_password",
        )
        read_only_fields = ("username", "role", "must_change_password")

    def get_batch(self, obj):
        b = obj.batch
        if not b:
            return None
        sub = b.current_subscription
        return {
            **BatchMiniSerializer(b).data,
            "is_active": sub is not None,
            "subscription_status": sub.status if sub else "inactive",
            "subscription_ends_at": sub.ends_at if sub else None,
        }


class ArtistProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    avatar = AbsoluteImageField(read_only=True)
    batch = BatchMiniSerializer(read_only=True)
    artwork_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = ("id", "username", "name", "bio", "avatar", "role", "batch", "artwork_count")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


class CollectorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "password", "display_name", "email", "phone")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate(self, attrs):
        password_validation.validate_password(attrs["password"], User(username=attrs["username"]))
        return attrs

    def create(self, validated):
        password = validated.pop("password")
        user = User(role=User.Role.COLLECTOR, **validated)
        user.set_password(password)
        user.save()
        return user
