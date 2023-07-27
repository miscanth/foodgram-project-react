import django_filters
# from django.db.models import Q
from django import forms
from recipes.models import Ingredient, Recipe
from rest_framework import filters


class RecipeFilter(django_filters.FilterSet):
    CHOICES = ((True, 1), (False, 0))
    tags = django_filters.CharFilter(
        field_name='tags__slug', method='filter_tags'
    )
    # NumberFilter
    is_favorited = django_filters.BooleanFilter(
        field_name='favourite_recipe', method='filter_is_favorited',
        widget=forms.RadioSelect(attrs={'class': 'form-control'},
                                 choices=CHOICES),)
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='recipe_shopping_cart', method='filter_is_in_shopping_cart',
        widget=forms.RadioSelect(attrs={'class': 'form-control'},
                                 choices=CHOICES),)

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(favourite_recipe__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(
                recipe_shopping_cart__user=self.request.user)

    def filter_tags(self, queryset, name, value):
        tags_list = self.request.GET.getlist('tags')
        return queryset.filter(tags__slug__in=tags_list).distinct()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']


class CustomSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        query = self.request.GET.get('search')
        list_1 = Ingredient.objects.filter(
            name__startswith=query).order_by('name')
        # list_2 = Ingredient.objects.filter(
        # name__icontains=query).order_by('name')
        return list_1
