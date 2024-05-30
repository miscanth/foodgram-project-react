from django.db import models
from user.models import User

from .validators import amount_validate, time_validate


class Tag(models.Model):
    """Класс для описания тэгов"""
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

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Класс для описания ингредиентов"""
    name = models.CharField(
        'Название',
        max_length=200,
        # unique=True,
        help_text='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=200,
        help_text='Единица измерения')

    class Meta:
        ordering = ('id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return self.name


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
    image = models.ImageField(
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Список id тегов',
        help_text='Список id тегов, к которым относится рецепт'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Список ингредиентов',
        help_text='Продукты для приготовления блюда по рецепту'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[time_validate],
        help_text='Время приготовления в минутах')
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
        help_text='Дата устанавливается автоматически'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author'
            )
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Класс для описания количества определённого ингредиента в рецепте"""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='recipe', verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='recipe_ingredients', verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[amount_validate],
        blank=False,
        help_text='Количество продукта в указанных единицах измерения'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'

    def __str__(self):
        return (f'{self.amount} {self.ingredient.measurement_unit} '
                f'{self.ingredient.name}')


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
        'Дата подписки',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Favourite(models.Model):
    """Класс для описания системы добавления рецептов в избранное"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Подписчик'
    )
    recipe = models.ForeignKey(
        Recipe,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='favors',
        verbose_name='Понравившийся рецепт'
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """Класс для описания системы добавления рецептов в список покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Подписчик'
    )
    recipe = models.ForeignKey(
        Recipe,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт, добавленный в список покупок'
    )
    pub_date = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'
