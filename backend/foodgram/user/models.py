from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Переопределенная модель Пользователя."""
    ADMIN = 'admin'
    USER = 'user'
    ROLES = [
        (ADMIN, 'Administrator'),
        (USER, 'User'),
    ]

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True
    )
    username = models.CharField(
        verbose_name='Логин пользователя',
        max_length=150,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+\Z')]
    )
    first_name = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия пользователя',
        max_length=150
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Статус подписки'
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=50,
        choices=ROLES,
        default=USER
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
