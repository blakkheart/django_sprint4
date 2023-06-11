from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

import datetime as dt

from core.models import PublishedAndCreatedModel


User = get_user_model()


class Category(PublishedAndCreatedModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        help_text=('Идентификатор страницы для URL; разрешены '
                   'символы латиницы, цифры, дефис и подчёркивание.'),
        verbose_name='Идентификатор',
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.title


class Location(PublishedAndCreatedModel):
    name = models.CharField(max_length=256, verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self) -> str:
        return self.name


class PublishedQueryset(models.QuerySet):

    def published(self, **optional_filter):
        return self.filter(**optional_filter,
                           is_published=True,
                           pub_date__lte=dt.datetime.now(tz=timezone.utc),
                           category__is_published=True,
                           )


class Post(PublishedAndCreatedModel):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        help_text=('Если установить дату и время '
                   'в будущем — можно делать отложенные публикации.'),
        verbose_name='Дата и время публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор публикации',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations',
        verbose_name='Местоположение',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='categories',
        verbose_name='Категория',
    )
    image = models.ImageField(
        blank=True,
        upload_to='posts_images',
        verbose_name='Фото',
    )
    objects = PublishedQueryset.as_manager()
    comment_count = models.PositiveIntegerField(
        default=0,
        blank=True,
        verbose_name='Количество комментариев',
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    text = models.TextField(verbose_name='Текст комментария')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         Post.objects.filter(pk=self.pk).update(comment_count=F('comment_count')+1)
    #     super().save(*args, **kwargs)

    class Meta:
        ordering = ('created_at',)
