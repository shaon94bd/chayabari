from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts import views as accounts
from apps.auctions.views import AuctionViewSet
from apps.batches import views as batches
from apps.gallery.views import ArtworkViewSet, ExhibitionViewSet
from apps.market.views import OrderViewSet
from apps.messaging import views as messaging

router = DefaultRouter()
router.register("artworks", ArtworkViewSet, basename="artwork")
router.register("exhibitions", ExhibitionViewSet, basename="exhibition")
router.register("auctions", AuctionViewSet, basename="auction")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    # auth & profile
    path("auth/login/", accounts.LoginView.as_view(), name="login"),
    path("auth/logout/", accounts.LogoutView.as_view(), name="logout"),
    path("auth/me/", accounts.MeView.as_view(), name="me"),
    path("auth/change-password/", accounts.ChangePasswordView.as_view(), name="change-password"),
    path("auth/register/", accounts.CollectorRegisterView.as_view(), name="register-collector"),
    path("artists/<str:username>/", accounts.ArtistProfileView.as_view(), name="artist-profile"),
    # batches & billing
    path("plans/", batches.PlanListView.as_view(), name="plans"),
    path("signup/", batches.SignupView.as_view(), name="signup"),
    path("batch/", batches.MyBatchView.as_view(), name="my-batch"),
    path("batch/members/", batches.MemberListCreateView.as_view(), name="members"),
    path("batch/members/<int:pk>/", batches.MemberDetailView.as_view(), name="member-detail"),
    path("batch/members/<int:pk>/reset-password/", batches.MemberResetPasswordView.as_view(), name="member-reset"),
    path("batch/members/<int:pk>/make-owner/", batches.TransferOwnershipView.as_view(), name="member-make-owner"),
    path("batch/subscription/", batches.SubscriptionView.as_view(), name="subscription"),
    path("batch/subscription/checkout/", batches.CheckoutView.as_view(), name="checkout"),
    path("public/batches/<slug:slug>/", batches.PublicBatchView.as_view(), name="public-batch"),
    # chat
    path("conversations/", messaging.ConversationListView.as_view(), name="conversations"),
    path("conversations/direct/", messaging.StartDirectView.as_view(), name="conversation-direct"),
    path("conversations/unread/", messaging.UnreadCountView.as_view(), name="conversation-unread"),
    path("conversations/<int:pk>/messages/", messaging.MessageListCreateView.as_view(), name="messages"),
] + router.urls
