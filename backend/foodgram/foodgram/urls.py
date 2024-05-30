from api import views
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'recipes/download_shopping_cart',
                views.GetShoppingCartView, basename='get_shopping_cart')
router.register(r'recipes', views.RecipeView, basename='recipe')
router.register(r'tags', views.TagView, 'tag')
router.register(r'ingredients', views.IngredientView, 'ingredient')
router.register(r'users/subscriptions',
                views.SubscriptionsView, basename='subscriptions')
router.register(r'users', views.UserView, 'user')
router.register(r'users/(?P<user_id>\d+)/subscribe', views.FollowView,
                basename='subscribe')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),
]

handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'
