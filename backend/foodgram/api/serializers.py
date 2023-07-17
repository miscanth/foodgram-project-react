import base64

import webcolors
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, Follow
from user.models import User
# from rest_framework.validators import UniqueTogetherValidator


class UserSerializer(serializers.ModelSerializer):
    """is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        author = get_object_or_404(User, username=obj.username)
        user=self.context['request'].user
        if Follow.objects.filter(user=user, author=author).exists():
            return True
        return False"""

    class Meta:
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')
        model = User


class RegisterDataSerializer(serializers.ModelSerializer):

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError("Username 'me' is not valid")
        return value

    class Meta:
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password')
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

        """current_recipe = get_object_or_404(Recipe, id=self.kwargs.get('id'))
        return RecipeIngredient.objects.filter(recipe=current_recipe.recipe_id)"""

class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = AddIngredientSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'image', 'cooking_time', 'author', 'tags', 'ingredients')
        # read_only_fields = ('author',)
        """validators = [
            UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'author')
            )
        ]"""

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

        if 'tags' not in validated_data:
            instance.save()
            return instance
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)

        if 'ingredients' not in validated_data:
            instance.save()
            return instance
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


class SubscriptionsSerializer(serializers.ModelSerializer):
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    """is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        author = get_object_or_404(User, username=obj.username)
        user=self.context['request'].user
        if Follow.objects.filter(user=user, author=author).exists():
            return True
        return False"""

    def get_recipes_count(self, obj):
        author = get_object_or_404(User, username=obj.username)
        return Recipe.objects.filter(author=author).count()

    class Meta:
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count') 
        model = User


class FollowProfileSerializer(serializers.ModelSerializer):
    # Подписаться на автора
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)
    author = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='username', required=True)

    def create(self, validated_data):
        author = validated_data.get('author')
        setattr(author, 'is_subscribed', True)
        author.save()
        follow = Follow.objects.create(**validated_data)
        return follow

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

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
        fields = ('id', 'user', 'author')
        read_only_fields = ('user',)
        model = Follow