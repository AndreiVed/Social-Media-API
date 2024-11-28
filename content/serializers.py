from django.contrib.auth import get_user_model
from rest_framework import serializers

from content.models import Hashtag, Post, Comment


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ("name",)


class PostSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Post
        fields = ("title", "content", "created_at", "hashtag", "image")


class PostListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="profile__full_name"
    )
    hashtag = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Post
        fields = ("id", "user", "title", "content", "created_at", "hashtag", "image")


class CommentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="profile__full_name"
    )
    post = serializers.SlugRelatedField(many=False, read_only=True, slug_field="title")

    class Meta:
        model = Comment
        fields = ("post", "user", "content", "created_at")
