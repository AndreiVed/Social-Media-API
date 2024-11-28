import os
import uuid

from django.db import models
from django.db.models import CASCADE
from django.utils.text import slugify

from social_media_api import settings


class Hashtag(models.Model):
    name = models.CharField(max_length=63)

    def __str__(self):
        return self.name


def post_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.id)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/post/", filename)


class Post(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=63, unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    hashtag = models.ManyToManyField(
        Hashtag, related_name="posts", null=True, blank=True
    )
    image = models.ImageField(null=True, blank=True, upload_to=post_image_file_path)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user}"

    @property
    def likes_count(self):
        return self.reactions.count("LIKE")

    @property
    def dislikes_count(self):
        return self.reactions.count("DISLIKE")

    @property
    def comments_count(self):
        return self.comments.count()


class PostReaction(models.Model):
    REACTION_CHOICES = {"LIKE": "Like", "DISLIKE": "Dislike"}
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="reactions"
    )
    post = models.ForeignKey(Post, on_delete=CASCADE, related_name="reactions")
    created_at = models.DateTimeField(auto_now_add=True)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)

    def __str__(self):
        return self.reaction


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
