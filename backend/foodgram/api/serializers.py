import base64

import webcolors

from django.core.files.base import ContentFile
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, Follow, Favourite, ShoppingCart
from user.models import User
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer


class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')
        model = User


class CustomUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name')


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

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    recipes = serializers.StringRelatedField(many=True, read_only=True)
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug', 'recipes')


class AddIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = AddIngredientSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        recipe = get_object_or_404(Recipe, name=obj.name)
        user=self.context['request'].user
        if Favourite.objects.filter(user=user, recipe=recipe).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        recipe = get_object_or_404(Recipe, name=obj.name)
        user=self.context['request'].user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return True
        return False

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')
        # read_only_fields = ('author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'author')
            )
        ]

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient_object = ingredient_data.get('ingredient')
            amount = ingredient_data.get('amount')
            added_ingredients = RecipeIngredient.objects.create(
                ingredient=ingredient_object, amount=amount
            )
            recipe.ingredients.add(added_ingredients)
            recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        if 'ingredients' not in validated_data and 'tags' not in validated_data:
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
            for ingredient_data in ingredients_data:
                ingredient_object = ingredient_data.get('ingredient')
                amount = ingredient_data.get('amount')
                updated_ingredients = RecipeIngredient.objects.create(
                    ingredient=ingredient_object, amount=amount
                )
                instance.ingredients.add(updated_ingredients)
                instance.save()
        return instance


class ShortListRecipeSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для укороченного обзора рецепта"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time') # 'image',


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = ShortListRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        author = get_object_or_404(User, username=obj.username)
        return Recipe.objects.filter(author=author).count()

    class Meta:
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = User


class FollowSerializer(serializers.ModelSerializer):
    # Подписаться на автора
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.ReadOnlyField(source='author.is_subscribed')
    recipes = RecipeSerializer(source='author.recipes', many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        follow = get_object_or_404(Follow, id=obj.id)
        return Recipe.objects.filter(author=follow.author).count()

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
                and Follow.objects.filter(user=user, author=author).exists()
        ):
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя!')
        return data

    class Meta:
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        model = Follow

class FavouriteSerializer(serializers.ModelSerializer):
    """Добавить выбранный рецепт в избранное"""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    # image = serializers.ReadOnlyField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        if (
                self.context['request'].method == 'POST'
                and Favourite.objects.filter(user=user, recipe=recipe).exists()
        ):
            raise serializers.ValidationError('Этот рецепт уже в избранном!')
        return data

    class Meta:
        model = Favourite
        fields = ('id', 'name', 'cooking_time') # 'image',


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Добавить выбранный рецепт в избранное"""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    # image = serializers.ReadOnlyField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    def validate(self, data):
        user = self.context['request'].user
        recipe_id = self.context.get('view').kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        if (
                self.context['request'].method == 'POST'
                and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
        ):
            raise serializers.ValidationError('Этот рецепт уже в списке покупок!')
        return data

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'cooking_time') #'image', 


class IngredientsInCartSerializer(serializers.ModelSerializer):
    """Список ингредиентов для приготовления рецептов из списка покупок"""
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'amount')


class GetShoppingCartSerializer(serializers.ModelSerializer):
    """Список ингредиентов для приготовления рецептов из списка покупок"""
    ingredients = IngredientsInCartSerializer(many=True, read_only=True, source='recipe.ingredients')

    class Meta:
        model = ShoppingCart
        fields = ('ingredients', )






    # author_id = self.context.get('view').kwargs.get('user_id')
    # author = get_object_or_404(User, pk=author_id)
    # author = get_object_or_404(User, id=self.kwargs.get('author_id'))
    # author = get_object_or_404(User, username=obj.username)
    # user = serializers.SlugRelatedField(slug_field='username', read_only=True)
    # author = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username', required=True)
    # user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    """is_subscribed = serializers.SerializerMethodField()
    def get_is_subscribed(self, obj):
        author = get_object_or_404(User, username=obj.username)
        user=self.context['request'].user
        if Follow.objects.filter(user=user, author=author).exists():
            return True
        return False"""
    
    """current_recipe = get_object_or_404(Recipe, id=self.kwargs.get('id'))
        return RecipeIngredient.objects.filter(recipe=current_recipe.recipe_id)"""
    
    """def delete(self, instance, validated_data):
    author = validated_data.get('author')
    setattr(author, 'is_subscribed', False)
    author.save()
    follow_id = validated_data.get('id')
    follow = Follow.objects.get_object_or_404(Follow, id=follow_id)
    follow.delete()"""

    """if 'ingredients' not in validated_data and 'tags' not in validated_data:
            instance.save()
            return instance
        elif 'tags' in validated_data and 'ingredients' not in validated_data:
            instance.tags.clear()
            tags_data = self.initial_data.get('tags')
            instance.tags.set(tags_data)
            instance.save()
            return instance
        elif 'ingredients' in validated_data and 'tags' not in validated_data:
            instance.ingredients.clear()
            ingredients_data = self.validated_data.get('ingredients')
            for ingredient_data in ingredients_data:
                ingredient_object = ingredient_data.get('ingredient')
                amount = ingredient_data.get('amount')
                updated_ingredients = RecipeIngredient.objects.create(
                    ingredient=ingredient_object, amount=amount
                )
                instance.ingredients.add(updated_ingredients)
                instance.save()
            return instance
        elif 'ingredients' and 'tags' in validated_data:
            instance.tags.clear()
            tags_data = self.initial_data.get('tags')
            instance.tags.set(tags_data)
            instance.ingredients.clear()
            ingredients_data = self.validated_data.get('ingredients')
            for ingredient_data in ingredients_data:
                ingredient_object = ingredient_data.get('ingredient')
                amount = ingredient_data.get('amount')
                updated_ingredients = RecipeIngredient.objects.create(
                    ingredient=ingredient_object, amount=amount
                )
                instance.ingredients.add(updated_ingredients)
                instance.save()
            return instance
        instance.save()
        return instance"""
    
    """if user == recipe.author:
            raise serializers.ValidationError(
                'Вы не можете добавить в избранное свои собственные рецепты!')
    
        if user == recipe.author:
            raise serializers.ValidationError(
                'Вы не можете добавить в список покупок свои собственные рецепты!')"""
    
    """def create(self, validated_data):
        recipe = validated_data.get('recipe')
        setattr(recipe, 'is_favourited', True)
        recipe.save()
        favourite = Favourite.objects.create(**validated_data)
        return favourite"""