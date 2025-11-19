from django.conf import settings
from django.db import models
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            # keep it simple and deterministic – tags are reused
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def meme_upload_to(instance, filename: str) -> str:
    # user based folder – keeps things tidy
    return f"memes/user_{instance.uploader_id}/{filename}"


class Album(TimeStampedModel):
    """
    Optional now, but ready for 'private albums' later.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="albums",
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Media(TimeStampedModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    uploader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="media_items",
    )
    title = models.CharField(max_length=150, blank=True)
    file = models.FileField(upload_to=meme_upload_to)
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
    )

    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_items",
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="media_items",
        blank=True,
    )

    # future proofing for private albums, etc.
    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Meme #{self.pk}"

    def delete(self, *args, **kwargs):
        """
        Ensure the file is removed from disk when the Media object is deleted.
        """
        storage = self.file.storage
        path = self.file.name

        # First delete the DB record
        super().delete(*args, **kwargs)

        # Then delete the actual file
        if path:
            storage.delete(path)

class Comment(TimeStampedModel):
    media = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="media_comments",
    )
    text = models.TextField(max_length=2000)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.media}"
