from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.auctions.models import Auction


class Command(BaseCommand):
    help = "Settle ended auctions (create orders for winners). Schedule hourly on PythonAnywhere."

    def handle(self, *args, **opts):
        n = 0
        for a in Auction.objects.filter(is_settled=False, is_cancelled=False, ends_at__lte=timezone.now()):
            a.settle()
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Settled {n} auction(s)."))
