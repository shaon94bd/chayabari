from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.auctions.models import Auction
from apps.core.testing import client_for, image_file, make_batch, make_collector, make_member, soon
from apps.gallery.models import Artwork
from apps.market.models import Order


class AuctionTests(TestCase):
    def setUp(self):
        self.batch, self.owner = make_batch()
        self.artist = make_member(self.batch, "mitu")
        self.art = Artwork.objects.create(batch=self.batch, artist=self.artist, title="Boat", image=image_file())
        self.buyer = make_collector()
        self.buyer2 = make_collector("buyer2")

    def create_auction(self, **kw):
        data = {"artwork_id": self.art.id, "starting_price": 5000, "min_increment": 500,
                "starts_at": soon(-1).isoformat(), "ends_at": soon(days=1).isoformat(), **kw}
        return client_for(self.artist).post("/api/auctions/", data, format="json")

    def test_bidding_rules(self):
        aid = self.create_auction().data["id"]
        url = f"/api/auctions/{aid}/bid/"
        self.assertEqual(client_for(self.buyer).post(url, {"amount": 4000}, format="json").status_code, 400)
        self.assertEqual(client_for(self.buyer).post(url, {"amount": 5000}, format="json").status_code, 201)
        res = client_for(self.buyer2).post(url, {"amount": 5200}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("5500", res.data["detail"])
        self.assertEqual(client_for(self.buyer2).post(url, {"amount": 5500}, format="json").status_code, 201)
        self.assertEqual(client_for(self.artist).post(url, {"amount": 9000}, format="json").status_code, 400)
        detail = client_for().get(f"/api/auctions/{aid}/").data
        self.assertEqual(detail["highest_bid"]["amount"], 5500)
        self.assertEqual(detail["minimum_next_bid"], 6000)
        self.assertNotIn("reserve_price", detail)

    def test_only_own_artwork(self):
        other = make_member(self.batch, "other")
        res = client_for(other).post("/api/auctions/", {"artwork_id": self.art.id, "starting_price": 1,
                                                         "starts_at": soon().isoformat(),
                                                         "ends_at": soon(days=1).isoformat()}, format="json")
        self.assertEqual(res.status_code, 400)

    @override_settings(AUCTION_EXTENSION_MINUTES=2)
    def test_anti_sniping_extension(self):
        aid = self.create_auction(ends_at=soon(1).isoformat()).data["id"]
        client_for(self.buyer).post(f"/api/auctions/{aid}/bid/", {"amount": 5000}, format="json")
        a = Auction.objects.get(pk=aid)
        self.assertGreater(a.ends_at, timezone.now() + timedelta(seconds=110))

    def test_settlement_creates_order_for_winner(self):
        aid = self.create_auction().data["id"]
        client_for(self.buyer).post(f"/api/auctions/{aid}/bid/", {"amount": 5000}, format="json")
        client_for(self.buyer2).post(f"/api/auctions/{aid}/bid/", {"amount": 7000}, format="json")
        Auction.objects.filter(pk=aid).update(ends_at=timezone.now() - timedelta(seconds=1))
        detail = client_for().get(f"/api/auctions/{aid}/").data
        self.assertTrue(detail["is_settled"])
        self.assertEqual(detail["winner"]["username"], "buyer2")
        order = Order.objects.get()
        self.assertEqual((order.buyer, order.amount_bdt, order.status), (self.buyer2, 7000, "accepted"))
        self.art.refresh_from_db()
        self.assertEqual(self.art.sale_status, "reserved")

    def test_reserve_not_met_no_sale(self):
        aid = self.create_auction(reserve_price=10000).data["id"]
        client_for(self.buyer).post(f"/api/auctions/{aid}/bid/", {"amount": 5000}, format="json")
        Auction.objects.filter(pk=aid).update(ends_at=timezone.now() - timedelta(seconds=1))
        from django.core.management import call_command

        call_command("settle_auctions", verbosity=0)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(Auction.objects.get(pk=aid).is_settled)

    def test_cancel_only_without_bids(self):
        aid = self.create_auction().data["id"]
        client_for(self.buyer).post(f"/api/auctions/{aid}/bid/", {"amount": 5000}, format="json")
        self.assertEqual(client_for(self.artist).post(f"/api/auctions/{aid}/cancel/").status_code, 400)
