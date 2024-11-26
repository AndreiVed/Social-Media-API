from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from user.views import (
    CreateUserView,
    ManageUserView,
    LogoutView,
    UserViewSet,
    FollowView,
    FollowersListView,
    FollowingListView,
)

app_name = "user"

urlpatterns = [
    path("", UserViewSet.as_view({"get": "list"}), name="list"),
    path("<int:pk>/", UserViewSet.as_view({"get": "retrieve"}), name="retrieve"),
    path("register/", CreateUserView.as_view(), name="create"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("<int:pk>/follow/", FollowView.as_view(), name="follow_profile"),
    path("<int:pk>/unfollow/", FollowView.as_view(), name="unfollow_profile"),
    path("<int:pk>/followers/", FollowersListView.as_view(), name="followers_list"),
    path("<int:pk>/following/", FollowingListView.as_view(), name="following_list"),
]
