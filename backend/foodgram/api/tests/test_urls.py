from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from user.models import User
from http import HTTPStatus
from django.core.cache import cache
from rest_framework.authtoken.models import Token


class RecipeURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='current_test_user', email='ff@ai.ru')
        cls.user_2 = User.objects.create_user(username='another_user', email='ff2@ai.ru')
        cls.tag = Tag.objects.create(
            name='Тестовый тэг',
            slug='test_slug',
            color='#49B61E',
        )
        cls.ingredient = Ingredient.objects.create(
            name='Тестовый ингредиент',
            measurement_unit='мл',
        )
        cls.recipe_ingredient = RecipeIngredient.objects.create(
            ingredient=cls.ingredient,
            amount=5,
        )
        cls.recipe = Recipe.objects.create(
            author=cls.user,
            text='Тестовый рецепт',
            name='Тестовое имя рецепта',
            cooking_time=10,
        )
        cls.recipe.tags.add(cls.tag)
        cls.recipe.ingredients.add(cls.recipe_ingredient)


    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='test',
            email='test@email.com',
            password='test',
        )
        token, created = Token.objects.get_or_create(user=self.user)
        self.client = Client(HTTP_AUTHORIZATION='Token ' + token.key)
        cache.clear()

    def test_urls_for_anonymous(self):
        """Проверка доступа ко всем страницам для
        анонимного пользователя.
        """
        urls_code_status = {
            '/api/recipes/': HTTPStatus.OK,
            f'/api/recipes/{self.recipe.pk}/': HTTPStatus.OK,
            f'/api/recipes/{self.recipe.pk}/favorite/': HTTPStatus.UNAUTHORIZED,
            f'/api/recipes/{self.recipe.pk}/shopping_cart/': HTTPStatus.UNAUTHORIZED,
            '/api/ingredients/': HTTPStatus.OK,
            '/api/tags/': HTTPStatus.UNAUTHORIZED,
            '/api/recipes/download_shopping_cart/': HTTPStatus.UNAUTHORIZED,
            '/api/users/': HTTPStatus.OK,
            f'/api/users/{self.user.pk}/': HTTPStatus.OK,
            f'/api/users/{self.user.pk}/subscribe/': HTTPStatus.UNAUTHORIZED,
            '/api/users/subscriptions/': HTTPStatus.UNAUTHORIZED,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status in urls_code_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)


    def test_urls_for_authorized(self):
            """Проверка доступа ко всем страницам для
            авторизированного пользователя.
            """
            urls_code_status = {
                '/api/recipes/': HTTPStatus.OK,
                f'/api/recipes/{self.recipe.pk}/': HTTPStatus.OK,
                '/api/recipes/download_shopping_cart/': HTTPStatus.OK,
                f'/api/recipes/{self.recipe.pk}/favorite/': HTTPStatus.METHOD_NOT_ALLOWED,
                f'/api/recipes/{self.recipe.pk}/shopping_cart/': HTTPStatus.METHOD_NOT_ALLOWED,
                '/unexisting_page/': HTTPStatus.NOT_FOUND,
                '/api/ingredients/': HTTPStatus.OK,
                '/api/tags/': HTTPStatus.FORBIDDEN,
            }
            for url, status in urls_code_status.items():
                with self.subTest(url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)