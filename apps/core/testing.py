from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.batches.serializers import SignupSerializer


def image_file(name="art.png", size=(40, 30), color=(200, 80, 40)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def make_batch(username="owner", batch_name="JU Fine Art 2021"):
    s = SignupSerializer(data=dict(
        username=username, password="s3cure-pass-99", display_name=username.title(),
        batch_name=batch_name, institution="Jahangirnagar University", session="2021-22",
    ))
    s.is_valid(raise_exception=True)
    owner = s.save()
    return owner.batch, owner


def make_member(batch, username):
    return User.objects.create_user(username=username, password="x-pass-12345", role="member", batch=batch,
                                    display_name=username.title())


def make_collector(username="buyer"):
    return User.objects.create_user(username=username, password="x-pass-12345", role="collector")


def client_for(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


def soon(minutes=0, **kw):
    return timezone.now() + timedelta(minutes=minutes, **kw)
