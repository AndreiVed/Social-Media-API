from django.contrib import admin

from content.models import Hashtag, Post, PostReaction, Comment

admin.site.register(Hashtag)
admin.site.register(Post)
admin.site.register(PostReaction)
admin.site.register(Comment)
