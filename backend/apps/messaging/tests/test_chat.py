from django.test import TestCase

from apps.core.testing import client_for, make_batch, make_collector, make_member


class ChatTests(TestCase):
    def setUp(self):
        self.batch, self.owner = make_batch()
        self.mitu = make_member(self.batch, "mitu")

    def test_group_chat_and_polling(self):
        convs = client_for(self.mitu).get("/api/conversations/").data
        group = next(c for c in convs if c["kind"] == "group")
        url = f"/api/conversations/{group['id']}/messages/"
        m1 = client_for(self.owner).post(url, {"body": "Meeting at 4pm in the studio"}, format="json").data
        self.assertEqual(client_for(self.mitu).get("/api/conversations/unread/").data["unread"], 1)
        msgs = client_for(self.mitu).get(url).data
        self.assertEqual(msgs[0]["body"], "Meeting at 4pm in the studio")
        self.assertEqual(client_for(self.mitu).get("/api/conversations/unread/").data["unread"], 0)
        client_for(self.mitu).post(url, {"body": "ok!"}, format="json")
        new = client_for(self.owner).get(f"{url}?after={m1['id']}").data
        self.assertEqual([m["body"] for m in new], ["ok!"])

    def test_other_batch_cannot_read_group(self):
        convs = client_for(self.mitu).get("/api/conversations/").data
        gid = convs[0]["id"]
        _, outsider = make_batch("o2", "DU")
        self.assertEqual(client_for(outsider).get(f"/api/conversations/{gid}/messages/").status_code, 404)

    def test_collector_dm_artist_but_not_collector(self):
        buyer = make_collector()
        res = client_for(buyer).post("/api/conversations/direct/", {"user_id": self.mitu.id}, format="json")
        self.assertEqual(res.status_code, 201)
        again = client_for(self.mitu).post("/api/conversations/direct/", {"user_id": buyer.id}, format="json")
        self.assertEqual(res.data["id"], again.data["id"])
        res = client_for(buyer).post("/api/conversations/direct/", {"user_id": make_collector("x").id}, format="json")
        self.assertEqual(res.status_code, 403)
