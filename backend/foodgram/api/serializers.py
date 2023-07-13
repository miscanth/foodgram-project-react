from rest_framework import serializers
from django.shortcuts import get_object_or_404
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    recipes = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug', 'recipes')


class AddIngredientInRecipeSerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    """ingredient = serializers.SlugRelatedField(
        queryset=Ingredient.objects.all(),
        slug_field='name', required=True)"""

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    """tags = serializers.SlugRelatedField(
        many=True, queryset=Tag.objects.all(),
        slug_field='slug', required=True)"""
    """ingredients = serializers.SlugRelatedField(
        many=True, queryset=Ingredient.objects.all(),
        slug_field='name', required=True)"""
    # image = Base64ImageField(required=False, allow_null=True)
    ingredients = AddIngredientInRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'author', 'cooking_time', 'tags', 'ingredients') # image



    def create(self, validated_data):
        # if 'ingredients' not in self.initial_data:
            # recipe = Recipe.objects.create(**validated_data)
            # return recipe
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient_object = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            added_ingredients = RecipeIngredient.objects.create(
                ingredient=ingredient_object, amount=amount
            )
            recipe.ingredients.add(added_ingredients)
            recipe.tags.set(tags)
        return recipe

    """def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        # if 'ingredients' not in validated_data:
            # instance.save()
            # return instance

        ingredients_data = validated_data.pop('ingredients')
        lst = []
        for ingredient in ingredients_data:
            current_ingredient, status = Ingredient.objects.get_or_create(
                **ingredient
            )
            lst.append(current_ingredient)
        instance.ingredients.set(lst)

        instance.save()
        return instance"""


