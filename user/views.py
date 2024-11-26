from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Profile
from .serializers import UserSerializer, FollowSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.settings import api_settings

from user.serializers import UserSerializer, AuthTokenSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = self.queryset
        email = self.request.query_params.get("email")
        username = self.request.query_params.get("username")
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")
        city = self.request.query_params.get("city")
        country = self.request.query_params.get("country")

        if email:
            queryset = queryset.filter(email__icontains=email)
        if username:
            queryset = queryset.filter(username__icontains=username)
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
        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"])
    def following(self, request):
        """
        List users the current user is following.
        """
        following = request.user.following.all()
        serializer = UserSerializer(following, many=True)
        return Response(serializer.data)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    permission_classes = (IsAuthenticated,)
    serializer_class = AuthTokenSerializer


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

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


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
