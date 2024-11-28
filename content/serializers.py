from django.contrib.auth import get_user_model
from rest_framework import serializers

from content.models import Hashtag, Post, Comment


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ("name",)


class PostSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    hashtag = HashtagSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Post
        fields = ("title", "content", "created_at", "hashtag", "image")

    def create(self, validate_data):
        hashtags_data = validate_data.pop("hashtag", [])
        post = Post.objects.create(**validate_data)

        for hashtag in hashtags_data:
            hashtag, _ = Hashtag.objects.get_or_create(name=hashtag["name"])
            post.hashtag.add(hashtag)

        return post


class PostListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="profile__full_name"
    )
    hashtag = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "title",
            "content",
            "created_at",
            "hashtag",
            "image",
            "comments_count",
        )


class CommentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    user = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="profile__full_name"
    )

    class Meta:
        model = Comment
        fields = ("id", "user", "created_at", "content")


class PostRetrieveSerializer(PostListSerializer):
    comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "title",
            "content",
            "created_at",
            "hashtag",
            "image",
            "comments",
        )
