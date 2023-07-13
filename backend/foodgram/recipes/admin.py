from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, Tag


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author'
    )
    # list_editable = ('tags',)
    search_fields = ('text',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = (
        'ingredient',
        'amount'
    )
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)

