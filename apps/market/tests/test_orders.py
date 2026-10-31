from django.test import TestCase

from apps.core.testing import client_for, image_file, make_batch, make_collector, make_member
from apps.gallery.models import Artwork


class OrderFlowTests(TestCase):
    def setUp(self):
        self.batch, self.owner = make_batch()
        self.artist = make_member(self.batch, "mitu")
        self.art = Artwork.objects.create(batch=self.batch, artist=self.artist, title="Boat", image=image_file(),
                                          price_bdt=8000, sale_status="available")
        self.buyer = make_collector()

    def order(self, user):
        return client_for(user).post("/api/orders/", {"artwork_id": self.art.id, "message": "Love it",
                                                      "contact_phone": "01700000000"}, format="json")

    def test_full_flow(self):
        res = self.order(self.buyer)
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["amount_bdt"], 8000)
        other = self.order(make_collector("b2")).data["id"]
        oid = res.data["id"]
        seller = client_for(self.artist)
        self.assertEqual(client_for(self.buyer).post(f"/api/orders/{oid}/accept/").status_code, 403)
        self.assertEqual(seller.post(f"/api/orders/{oid}/accept/").data["status"], "accepted")
        self.art.refresh_from_db()
        self.assertEqual(self.art.sale_status, "reserved")
        self.assertEqual(seller.get(f"/api/orders/{other}/").data["status"], "rejected")
        self.assertEqual(seller.post(f"/api/orders/{oid}/complete/").data["status"], "completed")
        self.art.refresh_from_db()
        self.assertEqual(self.art.sale_status, "sold")
        self.assertEqual(self.order(make_collector("b3")).status_code, 400)

    def test_cancel_accepted_returns_artwork_to_sale(self):
        oid = self.order(self.buyer).data["id"]
        client_for(self.artist).post(f"/api/orders/{oid}/accept/")
        client_for(self.buyer).post(f"/api/orders/{oid}/cancel/")
        self.art.refresh_from_db()
        self.assertEqual(self.art.sale_status, "available")

    def test_cannot_buy_own_or_unlisted(self):
        self.assertEqual(self.order(self.artist).status_code, 400)
        self.art.sale_status = "not_for_sale"
        self.art.save()
        self.assertEqual(self.order(self.buyer).status_code, 400)

    def test_orders_are_private(self):
        oid = self.order(self.buyer).data["id"]
        self.assertEqual(client_for(make_collector("nosy")).get(f"/api/orders/{oid}/").status_code, 404)
