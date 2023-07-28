from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import (UserViewSet
                          as BaseUserSetPasswordViewSet)
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from .filters import RecipeFilter
from .permissions import (IsAdmin, IsAuthorOrAdmin,
                          IsAuthor, ReadOnly, IsAdminOrReadOnly)
from .serializers import (ListRecipeSerializer, IngredientSerializer,
                          FavouriteSerializer, FollowSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserSerializer, UserRegistrationSerializer)

from recipes.models import (Ingredient, Favourite, Follow,
                            Recipe, ShoppingCart, Tag)
from user.models import User


class RecipeView(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrAdmin]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'list':
            return (ReadOnly(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return ListRecipeSerializer
        return RecipeSerializer


class TagView(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    #permission_classes = [IsAdmin]
    permission_classes = [IsAdminOrReadOnly]


class IngredientView(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


"""class UserSetPasswordView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SetPasswordSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(request.data)
        current_password = serializer.data['current_password']
        is_password_valid = self.request.user.check_password(current_password)
        if is_password_valid:
            self.request.user.set_password(serializer.data['new_password'])
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValidationError('invalid_password')"""


class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_permissions(self):
        if self.action == 'retrieve' or self.action == 'list':
            return (ReadOnly(),)
        if self.action == 'create':
            return (permissions.AllowAny(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def users_own_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated]
    )
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(request.data)
        current_password = serializer.data['current_password']
        is_password_valid = self.request.user.check_password(current_password)
        if is_password_valid:
            self.request.user.set_password(serializer.data['new_password'])
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValidationError('invalid_password')


class SubscriptionsView(viewsets.ModelViewSet):
    serializer_class = SubscriptionsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    http_method_names = ['get']

    def get_queryset(self):
        return User.objects.filter(is_subscribed=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FollowView(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsAuthor]

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        serializer.save(user=self.request.user, author=author)

    def delete(self, serializer, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        if (
                self.request.method == 'DELETE'
                and not Follow.objects.filter(
                    user=self.request.user, author=author).exists()
        ):
            raise ValidationError('Вы уже отписались от этого пользователя!')
        follow = get_object_or_404(
            Follow, user=self.request.user, author=author)
        follow.delete()
        setattr(author, 'is_subscribed', False)
        author.save()
        return Response('Успешная отписка', status=status.HTTP_204_NO_CONTENT)


class FavouriteView(viewsets.ModelViewSet):
    serializer_class = FavouriteSerializer
    queryset = Favourite.objects.all()
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    def delete(self, serializer, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        if (
                self.request.method == 'DELETE'
                and not Favourite.objects.filter(
                    user=self.request.user, recipe=recipe).exists()
        ):
            raise ValidationError('Вы уже удалили этот рецепт из избранного!')
        favourite = get_object_or_404(
            Favourite, user=self.request.user, recipe=recipe)
        favourite.delete()
        return Response(
            'Рецепт успешно удалён из избранного',
            status=status.HTTP_204_NO_CONTENT
        )


class ShoppingCartView(viewsets.ModelViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    def delete(self, serializer, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        if (
                self.request.method == 'DELETE'
                and not ShoppingCart.objects.filter(
                    user=self.request.user, recipe=recipe).exists()
        ):
            raise ValidationError(
                'Вы уже удалили этот рецепт из списка покупок!')
        shopping_cart = get_object_or_404(
            ShoppingCart, user=self.request.user, recipe=recipe)
        shopping_cart.delete()
        return Response(
            'Рецепт успешно удалён из списка покупок!',
            status=status.HTTP_204_NO_CONTENT
        )


class GetShoppingCartView(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [permissions.IsAuthenticated, IsAuthor]

    def list(self, request):
        shopping_list = ShoppingCart.objects.filter(user=self.request.user)
        shopping_dict = {}
        measure_dict = {}
        for cart in shopping_list:
            for ingredient_data in cart.recipe.ingredients.all():
                ingredient = ingredient_data.ingredient
                amount = ingredient_data.amount
                if ingredient.name not in shopping_dict.keys():
                    shopping_dict[ingredient.name] = amount
                    measure_dict[ingredient.name] = ingredient.measurement_unit
                else:
                    shopping_dict[ingredient.name] += amount

        filename = 'get_shopping_cart.txt'
        list = []
        list.append('СПИСОК ИНГРЕДИЕНТОВ\n')
        list.append('\n')
        count = 0
        for ingredient, amount in shopping_dict.items():
            count += 1
            string = (f'{count}. {ingredient} ({measure_dict[ingredient]}) '
                      f'- {amount}\n')
            list.append(string)

        response = HttpResponse(list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format(filename))
        return response
