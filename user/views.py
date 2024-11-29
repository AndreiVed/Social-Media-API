from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from content.permissions import IsOwnerOrReadOnly
from .models import User, Profile
from .serializers import (
    FollowSerializer,
    UserListAndRetrieveSerializer,
    ProfileSerializer,
    UserCreateAndUpdateSerializer,
    AuthTokenSerializer,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.settings import api_settings


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListAndRetrieveSerializer

    def get_queryset(self):
        queryset = self.queryset
        email = self.request.query_params.get("email")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        city = self.request.query_params.get("city")
        country = self.request.query_params.get("country")

        if email:
            queryset = queryset.filter(email__icontains=email)
        if first_name:
            queryset = queryset.filter(profile__first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(profile__last_name__icontains=last_name)
        if city:
            queryset = queryset.filter(profile__city__icontains=city)
        if country:
            queryset = queryset.filter(profile__country__icontains=country)

        return queryset

    @action(detail=True, methods=["POST"])
    def follow(self, request, pk=None):
        """
        Follow or unfollow a user.
        """
        user_to_follow = self.get_object()
        current_user_profile = request.user.profile

        serializer = FollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        if action == "follow":
            current_user_profile.followers.add(user_to_follow)
        elif action == "unfollow":
            current_user_profile.followers.remove(user_to_follow)

        return Response({"status": f"You have {action}ed {user_to_follow.username}"})

    @action(detail=False, methods=["GET"])
    def followers(self, request):
        """
        List followers of the current user.
        """
        followers = request.user.profile.followers.all()
        serializer = UserListAndRetrieveSerializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def following(self, request):
        """
        List users the current user is following.
        """
        following = request.user.following.all()
        serializer = UserListAndRetrieveSerializer(following, many=True)
        return Response(serializer.data)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserCreateAndUpdateSerializer
    permission_classes = [AllowAny]


class ManageUserView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserListAndRetrieveSerializer
        return UserCreateAndUpdateSerializer


class ManageProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user.profile


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer


class LogoutView(APIView):

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out"},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except KeyError:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class FollowView(APIView):

    def post(self, request, pk):
        """
        Follow a user by adding the authenticated user to their followers.
        """
        profile_to_follow = get_object_or_404(Profile, id=pk)

        if profile_to_follow.user == request.user:
            return Response(
                {"error": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_to_follow.followers.add(request.user)
        return Response(
            {"detail": "Successfully followed."}, status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        """
        Unfollow a user by removing the authenticated user from their followers.
        """
        profile_to_unfollow = get_object_or_404(Profile, id=pk)

        if profile_to_unfollow.user == request.user:
            return Response(
                {"error": "You cannot unfollow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_to_unfollow.followers.remove(request.user)
        return Response(
            {"detail": "Successfully unfollowed."}, status=status.HTTP_204_NO_CONTENT
        )


class FollowersListView(APIView):

    def get(self, request, pk):
        profile = get_object_or_404(Profile, id=pk)
        followers = profile.followers.all()
        data = [
            {"id": user.id, "full_name": user.profile.full_name} for user in followers
        ]
        return Response(data, status=status.HTTP_200_OK)


class FollowingListView(APIView):

    def get(self, request, pk):
        profile = get_object_or_404(Profile, id=pk)
        following = profile.user.following.all()
        data = [
            {"id": user.id, "full_name": user.profile.full_name} for user in following
        ]
        return Response(data, status=status.HTTP_200_OK)
