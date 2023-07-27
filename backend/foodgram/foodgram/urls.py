"""foodgram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from api import views
#from api.views import set_password


router = routers.DefaultRouter()
router.register(r'recipes/download_shopping_cart', views.GetShoppingCartView, basename='get_shopping_cart')
router.register(r'recipes', views.RecipeView, basename='recipe')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite', views.FavouriteView, basename='favourite')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart', views.ShoppingCartView, basename='shopping_cart')
router.register(r'tags', views.TagView, 'tag')
router.register(r'ingredients', views.IngredientView, 'ingredient')
router.register(r'users/subscriptions', views.SubscriptionsView, basename='subscriptions')
# router.register(r'users/set_password', views.UserSetPasswordView, basename='SetPassword')
router.register(r'users', views.UserView, 'user')
router.register(r'users/(?P<user_id>\d+)/subscribe', views.FollowView, basename='subscribe')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'