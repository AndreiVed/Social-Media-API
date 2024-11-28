from datetime import datetime

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from content.models import Hashtag, Post, Comment
from content.serializers import (
    HashtagSerializer,
    PostSerializer,
    CommentSerializer,
    PostListSerializer,
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


class PostViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Post.objects.all()

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
        if self.request.method == "GET":
            return PostListSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
