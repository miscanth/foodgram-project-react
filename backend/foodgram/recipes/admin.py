from django.contrib import admin

from .models import (Favourite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'fav_count'
    )
    search_fields = ('text',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'
    inlines = (RecipeIngredientInLine, )

    def fav_count(self, obj):
        recipe = Recipe.objects.get(id=obj.id)
        return recipe.favors.count()


class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'author'
    )
    list_filter = ('user', 'author')
    empty_value_display = '-пусто-'


class FavouriteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ingredient',
        'amount'
    )
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favourite, FavouriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Tag)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
