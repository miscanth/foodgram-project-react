import django_filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(
        field_name='tags__slug', method='filter_tags'
    )
    is_favorited = django_filters.NumberFilter(
        field_name='is_favorited', method='filter_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(favors__user=self.request.user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(
                shopping_cart__user=self.request.user)

    def filter_tags(self, queryset, name, value):
        tags_list = self.request.GET.getlist('tags')
        return queryset.filter(tags__slug__in=tags_list).distinct()

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']


class IngredientFilter(django_filters.FilterSet):
    """Поиск по названию ингредиента."""
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name', )
