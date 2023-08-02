from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer

from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from .filters import RecipeFilter
from .permissions import (IsAuthorOrAdmin,
                          IsAuthor, ReadOnly, IsAdminOrReadOnly)
from .serializers import (ListRecipeSerializer, IngredientSerializer,
                          FollowSerializer, RecipeSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserSerializer, UserRegistrationSerializer)

from recipes.models import (Ingredient, Favourite, Follow,
                            Recipe, RecipeIngredient, ShoppingCart, Tag)
from user.models import User


class TagView(viewsets.ModelViewSet):
    """Метод для получения списка тэгов"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class IngredientView(viewsets.ModelViewSet):
    """Метод для получения списка ингредиентов"""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name', ]
    pagination_class = None


class UserView(viewsets.ModelViewSet):
    """Метод для модели пользователя"""
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
    """Метод для получения списка - Мои подписки"""
    serializer_class = SubscriptionsSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    http_method_names = ['get']

    def get_queryset(self):
        return User.objects.filter(is_subscribed=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FollowView(viewsets.ModelViewSet):
    """Метод для подписки и отписки от пользователей"""
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    pagination_class = None

    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        serializer.save(user=self.request.user, author=author)

    def delete(self, serializer, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        if (
                self.request.method == 'DELETE'
                and not self.request.user.follower.filter(
                    author=author).exists()
        ):
            setattr(author, 'is_subscribed', False)
            author.save()
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow = get_object_or_404(
            Follow, user=self.request.user, author=author)
        follow.delete()
        setattr(author, 'is_subscribed', False)
        author.save()
        return Response('Успешная отписка', status=status.HTTP_204_NO_CONTENT)


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

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite_recipe(self, request, pk=None):
        """Метод добавления и удаления рецепта из избранного."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favourite.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт успешно добавлен в избранное.'},
                status=status.HTTP_201_CREATED,
            )
        elif (
                request.method == 'DELETE'
                and not request.user.favorites.filter(recipe=recipe).exists()
        ):
            return Response(
                    {'detail': 'Рецепт не был добавлен в избранное'
                     'Его нельзя удалить.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        favourite = get_object_or_404(
            Favourite, user=self.request.user, recipe=recipe)
        favourite.delete()
        return Response(
                {'detail': 'Рецепт успешно удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None) -> Response:
        """Метод добавления/удаления рецепта из корзины покупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if user.shopping_cart.filter(recipe=recipe).exists():
                return Response(
                    {'detail': 'Этот рецепт уже в списке покупок!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт успешно добавлен в корзину покупок.'},
                status=status.HTTP_201_CREATED,
            )
        elif (
                request.method == 'DELETE'
                and not self.request.user.shopping_cart.filter(
                    recipe=recipe).exists()
        ):
            return Response(
                {'detail': 'Рецепт не был добавлен в корзину покупок.'
                 ' Его нельзя удалить.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shopping_cart = get_object_or_404(
            ShoppingCart, user=self.request.user, recipe=recipe)
        shopping_cart.delete()
        return Response(
            {'detail': 'Рецепт успешно удалён из списка покупок!'},
            status=status.HTTP_204_NO_CONTENT,
        )


class GetShoppingCartView(viewsets.ModelViewSet):
    http_method_names = ['get']
    permission_classes = [permissions.IsAuthenticated, IsAuthor]

    def list(self, request):
        shopping_list = ShoppingCart.objects.filter(user=self.request.user)
        shopping_dict = {}
        measure_dict = {}
        for cart in shopping_list:
            for ingredient in cart.recipe.ingredients.all():
                recipe_ingredient = get_object_or_404(
                    RecipeIngredient, recipe=cart.recipe,
                    ingredient=ingredient)
                amount = recipe_ingredient.amount
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
