from django.test import TestCase

from apps.core.testing import client_for, image_file, make_batch, make_member, soon
from apps.gallery.models import Artwork


class ArtworkTests(TestCase):
    def setUp(self):
        self.batch, self.owner = make_batch()
        self.artist = make_member(self.batch, "mitu")

    def create_art(self, user=None, **extra):
        data = {"title": "River at dusk", "medium": "Oil on canvas", "image": image_file(size=(3000, 2000)), **extra}
        return client_for(user or self.artist).post("/api/artworks/", data, format="multipart")

    def test_create_artwork_shrinks_image(self):
        res = self.create_art(price_bdt=12000, for_sale=True)
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["sale_status"], "available")
        art = Artwork.objects.get()
        self.assertLessEqual(max(art.image.width, art.image.height), 1600)
        self.assertTrue(art.image.name.endswith(".jpg"))

    def test_for_sale_requires_price(self):
        res = self.create_art(for_sale=True)
        self.assertEqual(res.status_code, 400)
        self.assertIn("price_bdt", res.data)

    def test_public_listing_and_privacy(self):
        self.create_art()
        self.create_art(title="Draft", is_published=False)
        public = client_for().get("/api/artworks/").data["results"]
        self.assertEqual([a["title"] for a in public], ["River at dusk"])
        mine = client_for(self.artist).get("/api/artworks/?mine=1").data["results"]
        self.assertEqual(len(mine), 2)

    def test_only_artist_can_edit(self):
        art_id = self.create_art().data["id"]
        res = client_for(self.owner).patch(f"/api/artworks/{art_id}/", {"title": "Hacked"}, format="json")
        self.assertEqual(res.status_code, 403)
        res = client_for(self.artist).patch(f"/api/artworks/{art_id}/", {"title": "New"}, format="json")
        self.assertEqual(res.data["title"], "New")

    def test_exhibition_with_artworks(self):
        a1 = self.create_art().data["id"]
        a2 = self.create_art(title="Second").data["id"]
        other_batch, other_owner = make_batch("o2", "DU")
        foreign = self.create_art(user=other_owner, title="Foreign").data["id"]
        payload = {"title": "Graduation Show", "starts_at": soon(-60).isoformat(), "ends_at": soon(days=7).isoformat(),
                   "venue": "Zainul Gallery", "artwork_ids": [a2, a1]}
        res = client_for(self.owner).post("/api/exhibitions/", payload, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        detail = client_for().get(f"/api/exhibitions/{res.data['id']}/").data
        self.assertEqual([a["id"] for a in detail["artworks"]], [a2, a1])
        self.assertEqual(detail["phase"], "ongoing")
        res = client_for(self.owner).post("/api/exhibitions/", {**payload, "artwork_ids": [foreign]}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_collector_cannot_create_artwork(self):
        from apps.core.testing import make_collector

        res = self.create_art(user=make_collector())
        self.assertEqual(res.status_code, 403)
