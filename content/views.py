from datetime import datetime

from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from content.models import Hashtag, Post, Comment, PostReaction
from content.permissions import IsOwnerOrReadOnly
from content.serializers import (
    HashtagSerializer,
    PostSerializer,
    CommentSerializer,
    PostListSerializer,
    PostRetrieveSerializer,
    ReactionSerializer,
)


class HashtagViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Hashtag.objects.all()
    serializer_class = HashtagSerializer


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Post.objects.filter(user=self.request.user)
        title = self.request.query_params.get("title")
        hashtag = self.request.query_params.get("hashtag")
        date = self.request.query_params.get("date")

        if self.request.user.following:
            for user in self.request.user.following.all():
                queryset = Post.objects.filter(user__in=(self.request.user.id, user.id))

        if title:
            queryset = queryset.filter(title__icontains=title)

        if hashtag:
            queryset = queryset.filter(hashtag__name__icontains=hashtag)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__icontains=date)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostRetrieveSerializer
        if self.action == "create_comment":
            return CommentSerializer
        if self.action in ("like_post", "dislike_post"):
            return ReactionSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="add-comment")
    def create_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _handle_reaction(self, post, reaction_type):
        try:
            reaction = PostReaction.objects.get(
                user=self.request.user,
                post=post,
            )
            if reaction.reaction == reaction_type:
                reaction.delete()
                return Response(
                    {f"{reaction_type.lower()}": f"{reaction_type} removed."},
                    status=status.HTTP_200_OK,
                )

            reaction.reaction = reaction_type
            reaction.save()

            return Response(
                {f"{reaction_type.lower()}": f"Changed to {reaction_type}."},
                status=status.HTTP_200_OK,
            )
        except PostReaction.DoesNotExist:
            PostReaction.objects.create(
                user=self.request.user, post=post, reaction=reaction_type
            )
            return Response(
                {f"{reaction_type.lower()}": f"{reaction_type} added."},
                status=status.HTTP_201_CREATED,
            )

    @action(detail=True, methods=["post"], url_path="like")
    def like_post(self, request, pk=None):
        post = self.get_object()
        return self._handle_reaction(post, "LIKE")

    @action(detail=True, methods=["post"], url_path="dislike")
    def dislike_post(self, request, pk=None):
        post = self.get_object()
        return self._handle_reaction(post, "DISLIKE")

    @action(detail=False, methods=["get"], url_path="liked-posts")
    def liked_posts(self, request):
        liked_posts = Post.objects.filter(
            reactions__user=self.request.user, reactions__reaction="LIKE"
        ).distinct()
        serializer = PostListSerializer(liked_posts, many=True)
        return Response(serializer.data)


class CommentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
