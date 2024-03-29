from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.validators import validate_regex_username, validate_username
from .validators import valid_year


class NameSlug(models.Model):
    """Абстрактный родительский класс для моделей категория и жанр."""
    name = models.CharField(max_length=settings.NAME_TEXT_LENGTH,
                            unique=True,
                            blank=False,
                            verbose_name='имя')
    slug = models.SlugField(max_length=settings.SLUG_LENGTH,
                            unique=True,
                            blank=False,
                            verbose_name='slug')

    class Meta:
        abstract = True
        ordering = ('name',)
        verbose_name = 'Базовая модель'
        verbose_name_plural = 'Базовые модели'

    def __str__(self):
        return self.name


class Category(NameSlug):
    """Модель категория."""

    class Meta(NameSlug.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(NameSlug):
    """Модель жанр."""

    class Meta(NameSlug.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Модель Тайтла."""
    name = models.CharField(
        blank=False,
        max_length=settings.NAME_TEXT_LENGTH,
        verbose_name='Название произведения',)
    year = models.PositiveSmallIntegerField(
        blank=False,
        verbose_name='Год произведения',
        db_index=True,
        validators=(valid_year,))
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание произведения',)
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        verbose_name='Жанр произведения',)
    category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='titles',
        verbose_name='Категория произведения',)

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    """Класс для объединения жанров и произведений."""
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name='ID жанра'
    )

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='ID произведения'
    )


class User(AbstractUser):
    """Модель пользователя."""
    username = models.CharField(
        'Никнейм',
        max_length=settings.USERNAME_MAX_LENGHT,
        null=False,
        blank=False,
        unique=True,
        validators=(validate_regex_username,
                    validate_username),
    )
    email = models.EmailField(
        'Email',
        max_length=settings.EMAIL_MAX_LENGHT,
        null=False,
        unique=True,
        blank=False,
    )
    role = models.CharField(
        'Статус пользователя',
        max_length=max(
            len(role) for role, translated in settings.USER_ROLE_CHOICES),
        choices=settings.USER_ROLE_CHOICES,
        default=settings.USER,
    )
    first_name = models.CharField(
        max_length=settings.FIRST_USERNAME_MAX_LENGHT,
        blank=True,
    )
    last_name = models.CharField(
        max_length=settings.LAST_USERNAME_MAX_LENGHT,
        blank=True,
    )
    bio = models.TextField(
        'Биография',
        blank=True
    )
    confirmation_code = models.CharField(
        max_length=settings.CONFIRMATION_CODE_MAX_LENGHT,
        default='not defined yet',
        blank=True
    )

    class Meta:
        ordering = ('username', )
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return (self.role == settings.ADMIN
                or self.is_superuser or self.is_staff)

    @property
    def is_moderator(self):
        return self.role == settings.MODERATOR

    def __str__(self):
        return f'Пользователь - {self.username}'


class PublicAuthor(models.Model):
    """Базовый класс для Ревью и комментов."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(
        blank=False,
        null=False,
        verbose_name='Текст',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ('pub_date',)

    def __str__(self):
        return self.text[:settings.REVIEW_COMMENT_LENGHT]


class Review(PublicAuthor):
    """Модель отзыва."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение',
    )
    score = models.SmallIntegerField(
        blank=False,
        null=False,
        verbose_name='Оценка',
        validators=[
            MaxValueValidator(10, "Оценка не должна больше 10."),
            MinValueValidator(1, "Оценка не должна меньше 1.")
        ]
    )

    class Meta(PublicAuthor.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_author_review'
            )
        ]
        default_related_name = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Comment(PublicAuthor):
    """Модель Комменты."""
    review = models.ForeignKey(
        Review,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Комментарии',
    )

    class Meta(PublicAuthor.Meta):
        default_related_name = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
