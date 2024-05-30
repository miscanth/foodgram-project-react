import base64

import webcolors
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import \
    UserCreateSerializer as BaseUserRegistrationSerializer
from recipes.models import Follow, Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from user.models import User


class UserRegistrationSerializer(BaseUserRegistrationSerializer):
    """Сериализатор для регистрации пользователя"""
    class Meta(BaseUserRegistrationSerializer.Meta):
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор для User"""
    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')
        model = User


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов"""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class ListAddIngredientSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для поля рецепта
    ingredients с развёрнутой информацией"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(
        max_value=settings.QUANTITY_MAX, min_value=settings.QUANTITY_MIN)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ListRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для get-действий retrieve и list:
    получение списка и экземпляра объекта Recipe"""
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = ListAddIngredientSerializer(
        many=True, source='recipe_ingredients')
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField(
        max_value=settings.QUANTITY_MAX, min_value=settings.QUANTITY_MIN)

    def get_is_favorited(self, obj):
        recipe = get_object_or_404(Recipe, name=obj.name)
        user = self.context['request'].user
        if user.is_authenticated:
            if user.favorites.filter(recipe=recipe).exists():
                return True
        return False

    def get_is_in_shopping_cart(self, obj):
        recipe = get_object_or_404(Recipe, name=obj.name)
        user = self.context['request'].user
        if user.is_authenticated:
            if user.shopping_cart.filter(recipe=recipe).exists():
                return True
        return False

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = ('author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'author')
            )
        ]


class AddIngredientSerializer(serializers.ModelSerializer):
    """Укороченный вложенный сериализатор
    для создания/изменения рецепта"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')
    amount = serializers.IntegerField(
        max_value=settings.QUANTITY_MAX, min_value=settings.QUANTITY_MIN)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения рецепта"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = AddIngredientSerializer(
        many=True, source='ingredients.recipe_ingredients')
    cooking_time = serializers.IntegerField(
        max_value=settings.QUANTITY_MAX, min_value=settings.QUANTITY_MIN)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe_ingredient_data = ingredients_data.get('recipe_ingredients')
        data = []
        for recipe_ingredient in recipe_ingredient_data:
            RI = RecipeIngredient(
                ingredient=recipe_ingredient.get('ingredient'),
                amount=recipe_ingredient.get('amount'), recipe=recipe)
            data.append(RI)
        RecipeIngredient.objects.bulk_create(data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        if 'ingredients' not in validated_data and (
            'tags' not in validated_data
        ):
            instance.save()
            return instance
        if 'tags' in validated_data:
            instance.tags.clear()
            tags_data = self.initial_data.get('tags')
            instance.tags.set(tags_data)
            instance.save()
        if 'ingredients' in validated_data:
            instance.ingredients.clear()
            ingredients_data = self.validated_data.get('ingredients')
            recipe_ingredient_data = ingredients_data.get('recipe_ingredients')
            data = []
            for recipe_ingredient in recipe_ingredient_data:
                RI = RecipeIngredient(
                    ingredient=recipe_ingredient.get('ingredient'),
                    amount=recipe_ingredient.get('amount'), recipe=instance)
                data.append(RI)
            RecipeIngredient.objects.bulk_create(data)
            instance.save()
        return instance

    def to_representation(self, data):
        return ListRecipeSerializer(
            context=self.context).to_representation(data)


class ShortListRecipeSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для укороченного обзора рецепта"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Страница подписок"""
    # recipes = ShortListRecipeSerializer(many=True, read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        author = get_object_or_404(User, username=obj.username)
        return author.recipes.count()

    def get_recipes(self, obj):
        recipes_limit = (
            self.context.get('request').query_params.get('recipes_limit')
        )
        if recipes_limit:
            queryset = obj.recipes.all()[:int(recipes_limit)]
        else:
            queryset = obj.recipes.all()
        return ShortListRecipeSerializer(queryset, many=True).data

    class Meta:
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = User


class FollowSerializer(serializers.ModelSerializer):
    """Подписаться на автора"""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.ReadOnlyField(source='author.is_subscribed')
    recipes = ShortListRecipeSerializer(
        source='author.recipes', many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        follow = get_object_or_404(Follow, id=obj.id)
        return follow.author.recipes.count()

    def create(self, validated_data):
        author = validated_data.get('author')
        setattr(author, 'is_subscribed', True)
        author.save()
        follow = Follow.objects.create(**validated_data)
        return follow

    def validate(self, data):
        user = self.context['request'].user
        author_id = self.context.get('view').kwargs.get('user_id')
        author = get_object_or_404(User, pk=author_id)

        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя!')
        if (
                self.context['request'].method == 'POST'
                and user.follower.filter(author=author).exists()
        ):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!')
        return data

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = Follow
