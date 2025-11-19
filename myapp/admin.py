from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Tag, Album, Media, Comment


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "media_count", "created_at")
    search_fields = ("name", "slug")
    ordering = ("name",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # annotate how often a tag is used
        return qs.annotate(_media_count=Count("media_items"))

    @admin.display(ordering="_media_count", description="Used in memes")
    def media_count(self, obj):
        return obj._media_count


class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_private", "media_count", "created_at")
    search_fields = ("title", "owner__username", "owner__email")
    list_filter = ("is_private", "created_at")
    autocomplete_fields = ("owner",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_media_count=Count("media_items"))

    @admin.display(ordering="_media_count", description="Memes in album")
    def media_count(self, obj):
        return obj._media_count


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "text", "created_at")
    readonly_fields = ("author", "created_at")
    show_change_link = False


class MediaAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "id",
        "thumbnail",
        "title",
        "media_type",
        "uploader",
        "is_public",
        "album",
        "tag_list",
        "created_at",
    )
    list_select_related = ("uploader", "album")
    search_fields = (
        "title",
        "uploader__username",
        "uploader__email",
        "tags__name",
    )
    list_filter = (
        "media_type",
        "is_public",
        "album",
        "tags",
        "created_at",
    )
    date_hierarchy = "created_at"
    filter_horizontal = ("tags",)
    readonly_fields = ("preview", "created_at", "updated_at")
    inlines = [CommentInline]
    list_per_page = 50

    fieldsets = (
        (None, {
            "fields": ("title", "file", "media_type", "uploader", "album", "is_public")
        }),
        ("Tags", {
            "fields": ("tags",),
        }),
        ("Preview", {
            "fields": ("preview",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # prefetch tags to avoid N+1 in tag_list
        return qs.prefetch_related("tags", "uploader", "album")

    @admin.display(description="Preview")
    def thumbnail(self, obj):
        """
        Small preview in the list view.
        """
        if not obj.file:
            return "—"

        if obj.media_type == Media.MediaType.IMAGE:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;" />',
                obj.file.url,
            )
        elif obj.media_type == Media.MediaType.VIDEO:
            # you could make this fancier later with a generated thumbnail
            return "🎥"
        return "—"

    @admin.display(description="Tags")
    def tag_list(self, obj):
        names = [t.name for t in obj.tags.all()]
        return ", ".join(names) if names else "—"

    @admin.display(description="Preview (full)")
    def preview(self, obj):
        """
        Bigger preview on the detail page.
        """
        if not obj.file:
            return "No file"
        if obj.media_type == Media.MediaType.IMAGE:
            return format_html(
                '<img src="{}" style="max-width: 100%; max-height: 400px; border-radius: 6px;" />',
                obj.file.url,
            )
        elif obj.media_type == Media.MediaType.VIDEO:
            return format_html(
                '<video src="{}" controls style="max-width: 100%; max-height: 400px; border-radius: 6px;"></video>',
                obj.file.url,
            )
        return "Unsupported file type"


class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "media", "author", "created_at")
    search_fields = ("text", "author__username", "author__email", "media__title")
    list_filter = ("created_at", "author")
    date_hierarchy = "created_at"
    autocomplete_fields = ("media", "author")
    list_per_page = 50

    @admin.display(description="Comment")
    def short_text(self, obj):
        if len(obj.text) > 60:
            return obj.text[:57] + "..."
        return obj.text


admin.site.register(Tag, TagAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(Comment, CommentAdmin)
