from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from io import BytesIO
import csv, io
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa 
import pdfkit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .filters import RecipeFilter
from .permissions import (IsAdmin, IsAuthorOrAdmin,
                          IsAuthor, ReadOnly, IsAdminOrReadOnly)
from .serializers import (ListRecipeSerializer, IngredientSerializer,
                          FavouriteSerializer, FollowSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionsSerializer, TagSerializer,
                          UserSerializer, UserRegistrationSerializer)

from recipes.models import Ingredient, Favourite, Follow, Recipe, ShoppingCart, Tag
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
    permission_classes = [IsAdmin]


class IngredientView(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


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
        """serializer = SetPasswordSerializer(request.data)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)"""
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SubscriptionsView(viewsets.ModelViewSet):
    serializer_class = SubscriptionsSerializer
    permission_classes=[permissions.IsAuthenticated, IsAuthor]
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
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

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
    http_method_names = ['post', 'delete']
    permission_classes = [permissions.IsAuthenticated]

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
            string = f'{count}. {ingredient} ({measure_dict[ingredient]}) - {amount}\n'
            list.append(string)

        response = HttpResponse(list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response

        """template = get_template('api/get_shopping_cart.html')
        context = {
        'list': list,
        }
        html  = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='UTF-8')
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return None"""



