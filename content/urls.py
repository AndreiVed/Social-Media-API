from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from content.views import HashtagViewSet, PostViewSet, CommentViewSet
from user.views import (
    CreateUserView,
    ManageUserView,
    ManageProfileView,
    LogoutView,
    UserViewSet,
    FollowView,
    FollowersListView,
    FollowingListView,
)

app_name = "content"

router = routers.DefaultRouter()
router.register("comments", CommentViewSet)
router.register("", PostViewSet)


urlpatterns = [
    path("", include(router.urls)),
]
