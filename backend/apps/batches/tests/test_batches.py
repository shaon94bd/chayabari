from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.batches.models import Payment, Plan, Subscription
from apps.core.testing import client_for, make_batch, make_member


class SignupAndMembersTests(TestCase):
    def test_signup_creates_batch_owner_trial_and_group_chat(self):
        res = client_for().post("/api/signup/", {
            "username": "rafi", "password": "s3cure-pass-99", "display_name": "Rafi",
            "batch_name": "JU Fine Art 47", "institution": "Jahangirnagar University",
        }, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertIn("token", res.data)
        owner = User.objects.get(username="rafi")
        self.assertEqual(owner.role, "owner")
        self.assertTrue(owner.batch.is_active_subscription)
        self.assertEqual(owner.batch.current_subscription.status, "trial")
        self.assertTrue(hasattr(owner.batch, "group_chat"))

    def test_owner_bulk_adds_members_who_can_log_in(self):
        batch, owner = make_batch()
        res = client_for(owner).post("/api/batch/members/", {"members": [
            {"display_name": "Nusrat Jahan"}, {"display_name": "Tanvir Ahmed", "username": "tanvir"},
        ]}, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        creds = res.data["credentials"]
        self.assertEqual(len(creds), 2)
        self.assertEqual(creds[1]["username"], "tanvir")
        login = client_for().post("/api/auth/login/", {"username": creds[0]["username"],
                                                       "password": creds[0]["password"]}, format="json")
        self.assertEqual(login.status_code, 200)
        me = client_for(User.objects.get(username="tanvir")).get("/api/auth/me/")
        self.assertTrue(me.data["must_change_password"])
        self.assertEqual(me.data["batch"]["slug"], batch.slug)

    def test_member_cannot_add_members(self):
        batch, _ = make_batch()
        m = make_member(batch, "mitu")
        res = client_for(m).post("/api/batch/members/", {"display_name": "X"}, format="json")
        self.assertEqual(res.status_code, 403)

    @override_settings(TRIAL_MAX_MEMBERS=3)
    def test_seat_limit(self):
        batch, owner = make_batch()
        res = client_for(owner).post("/api/batch/members/", {"members": [
            {"display_name": "A"}, {"display_name": "B"}, {"display_name": "C"},
        ]}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(batch.members.count(), 1)

    def test_reset_password_and_change_password(self):
        batch, owner = make_batch()
        m = make_member(batch, "mitu")
        res = client_for(owner).post(f"/api/batch/members/{m.id}/reset-password/")
        self.assertEqual(res.status_code, 200)
        temp = res.data["password"]
        m.refresh_from_db()
        self.assertTrue(m.check_password(temp))
        res = client_for(m).post("/api/auth/change-password/", {"current_password": temp,
                                                                 "new_password": "my-own-secret-77"}, format="json")
        self.assertEqual(res.status_code, 200)
        m.refresh_from_db()
        self.assertFalse(m.must_change_password)

    def test_owner_cannot_touch_other_batch_members(self):
        _, owner = make_batch()
        other_batch, _ = make_batch("owner2", "DU Fine Art")
        stranger = make_member(other_batch, "stranger")
        res = client_for(owner).post(f"/api/batch/members/{stranger.id}/reset-password/")
        self.assertEqual(res.status_code, 404)

    def test_transfer_ownership(self):
        batch, owner = make_batch()
        m = make_member(batch, "mitu")
        res = client_for(owner).post(f"/api/batch/members/{m.id}/make-owner/")
        self.assertEqual(res.status_code, 200)
        m.refresh_from_db(); owner.refresh_from_db(); batch.refresh_from_db()
        self.assertEqual((m.role, owner.role, batch.owner_id), ("owner", "member", m.id))


class BillingTests(TestCase):
    def test_checkout_then_admin_verify_activates_plan(self):
        batch, owner = make_batch()
        plan = Plan.objects.get(code="year")
        res = client_for(owner).post("/api/batch/subscription/checkout/", {
            "plan": plan.id, "method": "bkash", "transaction_id": "9abc123xyz", "sender_number": "01711111111",
        }, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["status"], "pending")
        payment = Payment.objects.get()
        self.assertEqual(payment.transaction_id, "9ABC123XYZ")
        payment.verify()
        batch.refresh_from_db()
        sub = batch.current_subscription
        self.assertEqual((sub.status, sub.plan), ("active", plan))
        self.assertFalse(batch.subscriptions.filter(status="trial").exists())
        self.assertGreater((sub.ends_at - timezone.now()).days, 360)

    def test_duplicate_transaction_rejected(self):
        _, owner = make_batch()
        plan = Plan.objects.first()
        c = client_for(owner)
        c.post("/api/batch/subscription/checkout/", {"plan": plan.id, "method": "bkash", "transaction_id": "T1"}, format="json")
        _, owner2 = make_batch("o2", "Other")
        res = client_for(owner2).post("/api/batch/subscription/checkout/",
                                      {"plan": plan.id, "method": "bkash", "transaction_id": "t1"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_expired_batch_is_read_only_and_hidden(self):
        batch, owner = make_batch()
        Subscription.objects.filter(batch=batch).update(ends_at=timezone.now())
        res = client_for(owner).post("/api/exhibitions/", {}, format="json")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(client_for().get(f"/api/public/batches/{batch.slug}/").status_code, 404)
        # but the owner can still see billing and pay
        self.assertEqual(client_for(owner).get("/api/batch/subscription/").data["is_active"], False)


class TokenAuthTests(TestCase):
    def test_login_token_and_reset_logs_member_out(self):
        from rest_framework.test import APIClient

        batch, owner = make_batch()
        m = make_member(batch, "mitu")
        res = client_for().post("/api/auth/login/", {"username": "mitu", "password": "x-pass-12345"}, format="json")
        self.assertEqual(res.status_code, 200)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Token {res.data['token']}")
        self.assertEqual(c.get("/api/auth/me/").data["username"], "mitu")
        m.refresh_from_db()
        self.assertIsNotNone(m.last_login)
        client_for(owner).post(f"/api/batch/members/{m.id}/reset-password/")
        self.assertEqual(c.get("/api/auth/me/").status_code, 401)

    def test_wrong_password(self):
        res = client_for().post("/api/auth/login/", {"username": "nobody", "password": "x"}, format="json")
        self.assertEqual(res.status_code, 401)
