"""Create a demo batch with members, artworks, an exhibition, an auction and chat.

    python manage.py seed_demo            # owner login: demo_owner / demo-pass-123
"""

import random
from datetime import timedelta
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.accounts.models import User
from apps.auctions.models import Auction
from apps.batches.models import Batch
from apps.gallery.models import Artwork, Exhibition, ExhibitionItem
from apps.messaging.models import Conversation, Message

PASSWORD = "demo-pass-123"
PALETTES = [
    [(233, 196, 106), (244, 162, 97), (231, 111, 81), (38, 70, 83)],
    [(17, 75, 95), (2, 128, 144), (228, 253, 225), (69, 105, 144)],
    [(110, 68, 255), (184, 146, 255), (255, 194, 226), (255, 144, 179)],
    [(40, 54, 24), (96, 108, 56), (254, 250, 224), (221, 161, 94)],
]
TITLES = ["Monsoon over Padma", "Shapla in Bloom", "Old Dhaka Rooftops", "Fishermen at Dawn",
          "Silence of Kadam", "Rickshaw Dreams", "Mother and Child", "Red Earth", "Boatmen's Song", "Night Market"]
MEDIUMS = ["Oil on canvas", "Acrylic on canvas", "Watercolour on paper", "Woodcut print", "Mixed media"]


def abstract_painting(seed):
    rnd = random.Random(seed)
    pal = PALETTES[seed % len(PALETTES)]
    w, h = rnd.choice([(900, 1200), (1200, 900), (1000, 1000)])
    img = Image.new("RGB", (w, h), pal[0])
    d = ImageDraw.Draw(img)
    for _ in range(14):
        x, y = rnd.randint(-200, w), rnd.randint(-200, h)
        r = rnd.randint(80, 420)
        shape = rnd.choice(["ellipse", "rectangle"])
        getattr(d, shape)([x, y, x + r, y + r * rnd.uniform(0.4, 1.6)], fill=rnd.choice(pal))
    buf = BytesIO()
    img.save(buf, "JPEG", quality=85)
    return ContentFile(buf.getvalue(), name=f"demo-{seed}.jpg")


class Command(BaseCommand):
    help = "Seed a demo batch for local development."

    @transaction.atomic
    def handle(self, *args, **opts):
        if User.objects.filter(username="demo_owner").exists():
            self.stdout.write("Demo data already exists (demo_owner).")
            return
        batch = Batch.objects.create(name="JU Fine Art 2018-19", institution="Jahangirnagar University",
                                     session="2018-19", about="Final-year students of the Department of Fine Art.")
        batch.start_trial()
        owner = User(username="demo_owner", display_name="Rafiq Hasan", role="owner", batch=batch)
        owner.set_password(PASSWORD)
        owner.save()
        batch.owner = owner
        batch.save(update_fields=["owner"])
        members = [owner]
        for name in ["Nusrat Jahan", "Tanvir Ahmed", "Mitu Akter", "Sabbir Rahman"]:
            u = User(username=name.split()[0].lower(), display_name=name, role="member", batch=batch)
            u.set_password(PASSWORD)
            u.save()
            members.append(u)
        collector = User(username="collector", display_name="Farhana Collector", role="collector")
        collector.set_password(PASSWORD)
        collector.save()

        arts = []
        for i, title in enumerate(TITLES):
            artist = members[i % len(members)]
            for_sale = i % 3 != 0
            arts.append(Artwork.objects.create(
                batch=batch, artist=artist, title=title, medium=random.choice(MEDIUMS), year=2025,
                width_cm=random.choice([45, 60, 90]), height_cm=random.choice([60, 75, 120]),
                description="A study of light, memory and the rivers of Bengal.",
                image=abstract_painting(i), price_bdt=random.choice([6000, 9500, 15000, 22000]) if for_sale else None,
                sale_status="available" if for_sale else "not_for_sale",
            ))
        now = timezone.now()
        ex = Exhibition.objects.create(batch=batch, created_by=owner, title="Rivers & Roots — Graduation Show",
                                       description="Our final-year exhibition.", venue="Zainul Gallery, JU",
                                       starts_at=now - timedelta(days=2), ends_at=now + timedelta(days=12))
        ExhibitionItem.objects.bulk_create([ExhibitionItem(exhibition=ex, artwork=a, order=i) for i, a in enumerate(arts[:8])])
        Auction.objects.create(artwork=arts[0], batch=batch, created_by=arts[0].artist, starting_price=5000,
                               min_increment=500, starts_at=now - timedelta(hours=1), ends_at=now + timedelta(days=2))
        group = Conversation.group_for_batch(batch)
        for u, text in [(owner, "Welcome to Chayabari everyone! 🎨"), (members[1], "Hanging starts 10am tomorrow."),
                        (members[2], "I'll bring the frames.")]:
            Message.objects.create(conversation=group, sender=u, body=text)
        self.stdout.write(self.style.SUCCESS(
            f"Demo ready. Logins (password '{PASSWORD}'): demo_owner, nusrat, tanvir, mitu, sabbir, collector"))
