from rest_framework import status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from recipes.models import Ingredient, Favourite, Follow, Recipe, RecipeIngredient, ShoppingCart, Tag
from user.models import User
from .serializers import AddIngredientSerializer, GetShoppingCartSerializer, IngredientSerializer, FavouriteSerializer, FollowSerializer, RecipeSerializer, RegisterDataSerializer, ShoppingCartSerializer, SubscriptionsSerializer, TagSerializer, UserSerializer
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.decorators import api_view  # Импортировали декоратор
from rest_framework.response import Response  # Импортировали класс Response
from .permissions import IsOwnerOrReadOnly
from rest_framework.validators import ValidationError


class RecipeView(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagView(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientView(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class UserView(viewsets.ModelViewSet): # (viewsets.ReadOnlyModelViewSet):
    # lookup_field = 'username'
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterDataSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)

class SubscriptionsView(viewsets.ModelViewSet):
    serializer_class = SubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(is_subscribed=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CreateDeleteViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    pass 


class FollowView(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()
    # http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    #@action(methods=['create', 'delete'], detail=True)
    def perform_create(self, serializer):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        serializer.save(user=self.request.user, author=author)

    # @action(detail=True, methods=['DELETE'])
    def delete(self, serializer, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        if (
                self.request.method == 'DELETE'
                and not Follow.objects.filter(user=self.request.user, author=author).exists()
        ):
            raise ValidationError('Вы уже отписались от этого пользователя!')
        follow = get_object_or_404(Follow, user=self.request.user, author=author)
        follow.delete()
        setattr(author, 'is_subscribed', False)
        author.save()
        return Response('Успешная отписка', status=status.HTTP_204_NO_CONTENT)


class FavouriteView(viewsets.ModelViewSet):
    serializer_class = FavouriteSerializer
    queryset = Favourite.objects.all()
    # http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    #@action(methods=['create', 'delete'], detail=True)
    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    # @action(detail=True, methods=['DELETE'])
    def delete(self, serializer, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        if (
                self.request.method == 'DELETE'
                and not Favourite.objects.filter(user=self.request.user, recipe=recipe).exists()
        ):
            raise ValidationError('Вы уже удалили этот рецепт из избранного!')
        favourite = get_object_or_404(Favourite, user=self.request.user, recipe=recipe)
        favourite.delete()
        return Response('Рецепт успешно удалён из избранного', status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(viewsets.ModelViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    # http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    #@action(methods=['create', 'delete'], detail=True)
    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        serializer.save(user=self.request.user, recipe=recipe)

    # @action(detail=True, methods=['DELETE'])
    def delete(self, serializer, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        if (
                self.request.method == 'DELETE'
                and not ShoppingCart.objects.filter(user=self.request.user, recipe=recipe).exists()
        ):
            raise ValidationError('Вы уже удалили этот рецепт из списка покупок!')
        shopping_cart = get_object_or_404(ShoppingCart, user=self.request.user, recipe=recipe)
        shopping_cart.delete()
        return Response('Рецепт успешно удалён из списка покупок!', status=status.HTTP_204_NO_CONTENT)


class GetShoppingCartView(viewsets.ModelViewSet):
    serializer_class = GetShoppingCartSerializer
    queryset = ShoppingCart.objects.all()

    def perform_create(self, serializer):
        # shopping_list = ShoppingCart.objects.filter(user=self.request.user)
        serializer.save(user=self.request.user)
    



"""@api_view(['POST'])  # Применили декоратор и указали разрешённые методы
def follow(request, pk):
    author = User.objects.get(pk=pk)
    follow = Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    
    # if request.method == 'POST':
    serializer = FollowSerializer(author)
    return Response(serializer.data, status=status.HTTP_201_CREATED)"""
"""elif request.method == 'DELETE':
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)"""


"""def create(self, request):
        queryset = Follow.objects.all()
        author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        #author = get_object_or_404(queryset, pk=pk)
        serializer = FollowSerializer(author)
        return Response(serializer.data)"""
    
"""def get_author(self):
        get_object_or_404(User, id=self.kwargs.get('author_id'))"""

"""def get_queryset(self):
        return User.objects.get(user=self.get_author().id)"""

# author = User.objects.get(pk=self.request)
# author= self.context.get('kwargs').get('user_id')

"""def destroy(self, *args, **kwargs):
    serializer = self.get_serializer(self.get_object())
    super().destroy(*args, **kwargs)
    return Response(serializer.data, status=status.HTTP_200_OK)"""
"""def get_queryset(self):
    # Получаем id котика из эндпоинта
    cat_id = self.kwargs.get("cat_id")
    # И отбираем только нужные комментарии
    new_queryset = Comment.objects.filter(cat=cat_id)
    return new_queryset """

"""def get_queryset(self):
    review = get_object_or_404(
        Review,
        id=self.kwargs.get('review_id'),
        title__id=self.kwargs.get('title_id'))
    return review.comments.all()"""

"""def get_serializer_class(self):
    if self.action == 'create':
        return RecipeCreateSerializer
    return RecipeSerializer

def get_serializer_class(self):
    # Если запрошенное действие — получение одного объекта или списка
    if self.action == 'retrieve' or self.action == 'list':
        return GetTitleSerializer
    return RecipeSerializer"""

"""@action(detail=True, methods=['DELETE'])
    def delete(self, request, *args, **kwargs):
        # author = get_object_or_404(User, id=self.kwargs.get('user_id'))
        # author= self.context.get('kwargs').get('user_id')
        # author = User.objects.get(pk=self.request)
        # author_id = self.context.get('view').kwargs.get('user_id')
        # author = get_object_or_404(User, pk=author_id)
        # follow = get_object_or_404(Follow, user=request.user, author=author)
        # self.perform_destroy(follow)
        # follow.delete()
        #serializer.save(user=self.request.user, author=author)
        super().destroy(request, pk=self.kwargs.get('user_id'))
        return Response(status=status.HTTP_204_NO_CONTENT)"""

"""def perform_destroy(self, instance):
        instance.delete()"""