from datetime import datetime

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
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
    CommentListSerializer,
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


@extend_schema_view(
    list=extend_schema(
        summary="List Posts",
        description="Retrieve a list of posts for the authenticated user.",
        responses=PostListSerializer,
    ),
    retrieve=extend_schema(
        summary="Retrieve Post",
        description="Retrieve detailed information for a specific post.",
        responses=PostRetrieveSerializer,
    ),
    create=extend_schema(
        summary="Create Post",
        description="Create a new post.",
        request=PostSerializer,
        responses=PostSerializer,
    ),
    update=extend_schema(
        summary="Update Post",
        description="Update information for a specific post.",
        responses=PostRetrieveSerializer,
    ),
    partial_update=extend_schema(
        summary="Partial update Post",
        description="Partial update information for a specific post.",
        responses=PostRetrieveSerializer,
    ),
    destroy=extend_schema(
        summary="Delete Post",
        description="Delete a specific post.",
        responses=PostRetrieveSerializer,
    ),
)
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

    @extend_schema(
        summary="Create Comment for Post",
        responses=CommentSerializer,
    )
    @action(detail=True, methods=["post"], url_path="add-comment")
    def create_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _handle_reaction(self, post, reaction_type):
        # Toggle like/dislike logic
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

    @extend_schema(
        summary="Like Post",
        description="Toggle a like reaction for a specific post.",
        responses=ReactionSerializer,
    )
    @action(detail=True, methods=["post"], url_path="like")
    def like_post(self, request, pk=None):
        post = self.get_object()
        return self._handle_reaction(post, "LIKE")

    @extend_schema(
        summary="Dislike Post",
        description="Toggle a dislike reaction for a specific post.",
        responses=ReactionSerializer,
    )
    @action(detail=True, methods=["post"], url_path="dislike")
    def dislike_post(self, request, pk=None):
        post = self.get_object()
        return self._handle_reaction(post, "DISLIKE")

    @extend_schema(
        summary="View list of User's liked Posts",
        responses=PostListSerializer,
    )
    @action(detail=False, methods=["get"], url_path="liked-posts")
    def liked_posts(self, request):
        liked_posts = Post.objects.filter(
            reactions__user=self.request.user, reactions__reaction="LIKE"
        ).distinct()
        serializer = PostListSerializer(liked_posts, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List Posts with Search",
        description=(
            "Retrieve a list of posts for the authenticated user, optionally "
            "filtered by title, hashtag, or date. Users will see their posts "
            "and posts from users they are following."
        ),
        parameters=[
            OpenApiParameter(
                name="title",
                description="Filter posts by a partial match on the title.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="hashtag",
                description="Filter posts by a partial match on the hashtag name.",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="date",
                description="Filter posts by creation date (format: YYYY-MM-DD).",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: PostListSerializer,
            401: "Unauthorized - Authentication credentials were not provided.",
        },
    )
    def list(self, request, *args, **kwargs):
        """
        List posts with optional search parameters.
        """
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(
        summary="List of User Comments",
        description="Retrieve a list of posts for the authenticated user.",
        responses=PostListSerializer,
    ),
    retrieve=extend_schema(
        summary="Retrieve Comment",
        description="Retrieve detailed information for a specific comment.",
        responses=PostRetrieveSerializer,
    ),
    update=extend_schema(
        summary="Update Comment",
        description="Update information for a specific comment.",
        responses=PostRetrieveSerializer,
    ),
    partial_update=extend_schema(
        summary="Partial update Comment",
        description="Partial update information for a specific comment.",
        responses=PostRetrieveSerializer,
    ),
    destroy=extend_schema(
        summary="Delete Comment",
        description="Delete a specific post.",
        responses=PostRetrieveSerializer,
    ),
)
class CommentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
