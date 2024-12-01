from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
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

    @extend_schema(
        summary="Follow or Unfollow a User",
        description="Follow or unfollow a specific user. Use `action: 'follow'` to follow or `action: 'unfollow'` to unfollow.",
        request=FollowSerializer,
        responses={200: None},
    )
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

    @extend_schema(
        summary="List User Followers",
        description="Retrieve a list of followers for the currently authenticated user.",
        responses={200: UserListAndRetrieveSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"])
    def followers(self, request):
        """
        List followers of the current user.
        """
        followers = request.user.profile.followers.all()
        serializer = UserListAndRetrieveSerializer(followers, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List Users Followed",
        description="Retrieve a list of users that the currently authenticated user is following.",
        responses={200: UserListAndRetrieveSerializer(many=True)},
    )
    @action(detail=False, methods=["GET"])
    def following(self, request):
        """
        List users the current user is following.
        """
        following = request.user.following.all()
        serializer = UserListAndRetrieveSerializer(following, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List Users",
        description="Retrieve a list of all users with optional filters.",
        parameters=[
            OpenApiParameter(name="email", description="Filter by email", type=str),
            OpenApiParameter(
                name="first_name", description="Filter by first name", type=str
            ),
            OpenApiParameter(
                name="last_name", description="Filter by last name", type=str
            ),
            OpenApiParameter(name="city", description="Filter by city", type=str),
            OpenApiParameter(name="country", description="Filter by country", type=str),
        ],
        responses={200: UserListAndRetrieveSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a User",
        description="Retrieve details of a specific user by ID.",
        responses={200: UserListAndRetrieveSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserCreateAndUpdateSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a New User",
        description="Create a new user account by providing the required information.",
        request=UserCreateAndUpdateSerializer,
        responses={201: UserCreateAndUpdateSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


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

    @extend_schema(
        summary="Retrieve Current User",
        description="Retrieve details of the currently authenticated user.",
        responses={200: UserListAndRetrieveSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update Current User",
        description="Update the details of the currently authenticated user.",
        request=UserCreateAndUpdateSerializer,
        responses={200: UserCreateAndUpdateSerializer},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class ManageProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user.profile

    @extend_schema(
        summary="Retrieve User Profile",
        description="Retrieve the profile of the currently authenticated user.",
        responses={200: ProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update User Profile",
        description="Update the profile information of the currently authenticated user.",
        request=ProfileSerializer,
        responses={200: ProfileSerializer},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = AuthTokenSerializer


class LogoutView(APIView):

    @extend_schema(
        summary="Logout User",
        description="Logout the authenticated user by blacklisting their refresh token.",
        request=None,
        responses={205: {"detail": "Successfully logged out"}},
    )
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

    @extend_schema(
        summary="Follow a User",
        description="Follow a specific user by their profile ID.",
        responses={201: None},
    )
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

    @extend_schema(
        summary="Unfollow a User",
        description="Unfollow a specific user by their profile ID.",
        responses={204: None},
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

    @extend_schema(
        summary="List Followers of a User",
        description="Retrieve a list of all followers for a specific user by their profile ID.",
        responses={200: None},
    )
    def get(self, request, pk):
        profile = get_object_or_404(Profile, id=pk)
        followers = profile.followers.all()
        data = [
            {"id": user.id, "full_name": user.profile.full_name} for user in followers
        ]
        return Response(data, status=status.HTTP_200_OK)


class FollowingListView(APIView):

    @extend_schema(
        summary="List Users Followed by a User",
        description="Retrieve a list of users followed by a specific user by their profile ID.",
        responses={200: None},
    )
    def get(self, request, pk):
        profile = get_object_or_404(Profile, id=pk)
        following = profile.user.following.all()
        data = [
            {"id": user.id, "full_name": user.profile.full_name} for user in following
        ]
        return Response(data, status=status.HTTP_200_OK)
