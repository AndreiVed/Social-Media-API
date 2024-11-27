from django.shortcuts import render
from django.template.context_processors import request
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
        if self.request.user.following:
            for user in self.request.user.following.all():
                queryset = Post.objects.filter(user__in=(self.request.user.id, user.id))
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
