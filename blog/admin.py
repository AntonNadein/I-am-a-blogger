from django.contrib import admin

from blog.models import Blog, PaidBlog, Payment, Topic

admin.site.register(PaidBlog)
admin.site.register(Payment)


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    """Админка блога"""

    list_display = (
        "id",
        "title",
        "owner",
        "created_at",
        "is_published",
        "view_count",
    )
    list_filter = (
        "created_at",
        "owner",
        "is_published",
        "topic",
    )
    search_fields = ("title",)
    ordering = ("created_at",)
    list_display_links = ("title",)
    list_per_page = 20
    filter_horizontal = ("like",)
    fields = [
        "title",
        "topic",
        "blog_text",
        "image",
        ("owner", "is_paid"),
        ("view_count", "is_published"),
        "like",
    ]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """Админка тематик блогов"""

    list_display = (
        "id",
        "title",
        "description",
    )
    list_filter = ("title",)
    search_fields = ("title",)
    list_display_links = ("title",)
    ordering = ("title",)
    fields = [
        "title",
        "description",
    ]
