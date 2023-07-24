from rest_framework import status, viewsets
from rest_framework.response import Response
from io import BytesIO
import csv, io
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa 
from django.template import Context, Template
import pdfkit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.template import loader
from django.http import FileResponse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from recipes.models import Ingredient, Favourite, Follow, Recipe, RecipeIngredient, ShoppingCart, Tag
from user.models import User
from .serializers import AddIngredientSerializer, GetShoppingCartSerializer, IngredientSerializer, FavouriteSerializer, FollowSerializer, RecipeSerializer, ShoppingCartSerializer, SubscriptionsSerializer, TagSerializer, UserListSerializer, CustomUserSerializer
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.decorators import api_view  # Импортировали декоратор
from rest_framework.response import Response  # Импортировали класс Response
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from rest_framework.validators import ValidationError
# RegisterDataSerializer, UserEditSerializer,


class RecipeView(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagView(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [IsAdminOrReadOnly]


class IngredientView(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [IsAdminOrReadOnly]


class UserView(viewsets.ModelViewSet):
    # lookup_field = 'username'
    http_method_names = ['get', 'post']
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return UserListSerializer
        return CustomUserSerializer

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


class SubscriptionsView(viewsets.ModelViewSet):
    serializer_class = SubscriptionsSerializer
    permission_classes=[permissions.IsAuthenticated]

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
    http_method_names = ['post', 'delete']
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
    http_method_names = ['get']
    """serializer_class = GetShoppingCartSerializer
    # template_name = 'api/get_shopping_cart.html'

    def get_queryset(self):
        return ShoppingCart.objects.filter(user=self.request.user)"""

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

    
        """template = 'api/get_shopping_cart.html'
        context = {
        'list': list,
        }
        return render(request, template, context)"""

        
        """template = get_template('api/get_shopping_cart.html')
        context = {
        'list': list,
        }
        html  = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8') # , encoding='UTF-32'
        if not pdf.err:
            return HttpResponse(result.getvalue(), content_type='application/pdf')
        return None"""


        
        
        """pdfmetrics.registerFont(TTFont('OpenSans-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
        pdfmetrics.registerFont(TTFont('VeraIt', 'VeraIt.ttf'))
        pdfmetrics.registerFont(TTFont('VeraBI', 'VeraBI.ttf'))
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont('Vera', 32)
        p.drawString(100, 100, "Hello world dgdhрвпо.")
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="hello.pdf")"""


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

"""def list(self, request):
        shopping_list = ShoppingCart.objects.filter(user=self.request.user)
        check_list = []
        shopping_cart = []
        for cart in shopping_list:
            for ingredient_data in cart.recipe.ingredients.all():
                ingredient = ingredient_data.ingredient
                amount = ingredient_data.amount
                if ingredient not in check_list:
                    string = f'{ingredient.name} ({ingredient.measurement_unit}) - {amount}'
                    shopping_cart.append(string)
                    check_list.append(ingredient)
                
        return Response(shopping_cart)"""

"""def list(self, request):
        shopping_list = ShoppingCart.objects.filter(user=self.request.user)
        shopping_cart = {}
        for cart in shopping_list:
            for ingredient_data in cart.recipe.ingredients.all():
                ingredient = ingredient_data.ingredient
                amount = ingredient_data.amount
                if ingredient.name not in shopping_cart.keys():
                    shopping_cart[ingredient.name] = amount
                    # string = f'{ingredient.name} ({ingredient.measurement_unit}) - {amount}'
                    # shopping_cart.append(string)
                else:
                    shopping_cart[ingredient.name] += amount
        return Response(shopping_cart)"""