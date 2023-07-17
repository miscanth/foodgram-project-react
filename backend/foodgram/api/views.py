from rest_framework import status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from recipes.models import Ingredient, Follow, Recipe, RecipeIngredient, Tag
from user.models import User
from .serializers import AddIngredientSerializer, IngredientSerializer, FollowProfileSerializer, RecipeSerializer, RegisterDataSerializer, SubscriptionsSerializer, TagSerializer, UserSerializer
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
#  

class RecipeView(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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


class FollowView(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowProfileSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)