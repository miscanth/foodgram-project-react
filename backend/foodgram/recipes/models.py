from django.db import models
from django.contrib.auth import get_user_model

from .validators import amount_validate, time_validate
# from user.models import User

User = get_user_model()

class Tag(models.Model): # ^[-a-zA-Z0-9_]+$ Уникальный слаг
    # Класс для описания тэгов
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        help_text='Название тэга')
    color = models.CharField(max_length=7, unique=True)
    slug = models.SlugField('Индетификатор',
                            max_length=200,
                            unique=True,
                            db_index=True,
                            help_text=('Индетификатор тэга'))

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ('id',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Ingredient(models.Model):
    """Класс для описания ингредиентов"""
    name = models.CharField(
        'Название',
        max_length=200,
        unique=True,
        help_text='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=200,
        help_text='Единица измерения')

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ('id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

class RecipeIngredient(models.Model):
    """Класс для описания количества определённого ингредиента в рецепте"""
    # recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name = 'Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.IntegerField(
        'Количество',
        validators=[amount_validate],
        # required=True,
        help_text='Количество продукта в указанных единицах измерения'
    )

    class Meta:
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'

    def __str__(self):
        return f'{self.amount} {self.ingredient.measurement_unit} {self.ingredient.name}'


class Recipe(models.Model):
    """Класс для описания рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        'Название',
        max_length=200,
        help_text='Название рецепта')
    image = models.ImageField( # Картинка, закодированная в Base64
        upload_to='recipes/images/',
        # null=True,
        # default=None,
        # unique=True
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        # on_delete=models.SET_NULL,
        # null=True,
        related_name='recipes',
        verbose_name='Список id тегов',
        help_text='Список id тегов, к которым относится рецепт'
    )
    ingredients = models.ManyToManyField(
        RecipeIngredient,
        # through='RecipeIngredient',
        # on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Список ингредиентов',
        help_text='Продукты для приготовления блюда по рецепту'
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        validators=[time_validate],
        help_text='Время приготовления в минутах')
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
        help_text='Дата устанавливается автоматически'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'





class Follow(models.Model):
    """Класс для описания системы подписки на авторов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    # колонка для soft delete design pattern,
    # исправно работает , но в функции отписки во views.py
    # пришлось закомментить её реализацию, чтобы пройти тесты из репозитория
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Статус отписки'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        if not self.is_deleted:
            return f'{self.user} подписался на {self.author}'
        else:
            return f'{self.user} отписался от {self.author}'
