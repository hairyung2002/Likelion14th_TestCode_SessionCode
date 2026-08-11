from django.db import models
from django.conf import settings

# Create your models here.
class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)


def image_upload_path(instance, filename):
    return f'{instance.pk}/{filename}'


class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movies',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=50)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to=image_upload_path, blank=True, null=True)
    click_num = models.PositiveSmallIntegerField(default=0)


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    movie = models.ForeignKey(Movie, blank=False, null=False, on_delete=models.CASCADE, related_name='comments')
    writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='movie_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
