## Об авторе:
Меня зовут Юлия, и учусь в ЯндексПрактикуме в 21 когорте курса «Python-разработчик плюс».

# Проект Foodgram
Деплой проекта Foodgram в **Docker контейнерах** и **CI/CD** с помощью **GitHub Actions** на удалённый сервер

### Описание проекта и используемые технологии
Проект Foodgram - это приложение ***«Продуктовый помощник»***: сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 

Это полностью рабочий проект, который состоит из бэкенд-приложения на **Django** и фронтенд-приложения на **React**. Пользователь может получить доступ к проекту по следующему доменному имени: <  >

API для Foodgram написан с использованием библиотеки **Django REST Framework**, используется **TokenAuthentication** для аутентификации, а также подключена библиотека **Djoser**.

Проект размещён в **Docker** контейнерах на удалённом сервере. На удалённом сервере настроен веб-сервер **Nginx** для перенаправления запросов и для их шифрования по **протоколу HTTPS**. В контейнере бэкенда настроен **WSGI-сервер Gunicorn**.
Автоматизация тестирования и деплоя проекта Foodgram осуществлена с помощью **GitHub Actions**.

### Как запустить проект: 
Клонировать репозиторий и перейти в него в командной строке: 
```
git clone git@github.com:miscanth/foodgram-project-react.git
```
Cоздать и активировать виртуальное окружение: 
```
python3.9 -m venv venv 
```
* Если у вас Linux/macOS 

    ```
    source env/bin/activate
    ```
* Если у вас windows 
 
    ```
    source env/scripts/activate 
    ```
```
python3.9 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
```
cd backend/foodgram 
```
Выполнить миграции: 
```
python3.9 manage.py migrate 
```
Запустить проект:
```
python3.9 manage.py runserver
```

### Примеры запросов:

Пример GET-запроса с токеном пользователя holly: Просмотр рецепта с id 1.

*GET .../api/recipes/1/*

Пример ответа:
```
{
    "id": 1,
    "tags": [
        {
            "id": 2,
            "name": "breakfast",
            "color": "#49B60E",
            "slug": "breakfast"
        }
    ],
    "author": {
        "email": "ya@ya.ru",
        "id": 1,
        "username": "miscanth",
        "first_name": "",
        "last_name": "",
        "is_subscribed": false
    },
    "ingredients": [
        {
            "id": 2182,
            "name": "яйца куриные",
            "measurement_unit": "г",
            "amount": 1
        },
        {
            "id": 1032,
            "name": "молоко",
            "measurement_unit": "г",
            "amount": 100
        }
    ],
    "is_favorited": false,
    "is_in_shopping_cart": false,
    "name": "omlette",
    "image": "http://127.0.0.1:8000/recipes/images/21259e2676ae3710d680a854134d66b7_586NMPe.jpg",
    "text": "Omlette",
    "cooking_time": 12
}
```
Пример POST-запроса с токеном пользователя holly: подписка на пользователя с id 7.

*POST .../api/users/7/subscribe/*

Пример ответа:
```
{
    "email": "serf@ya.ru",
    "id": 7,
    "username": "molly",
    "first_name": "Molly",
    "last_name": "Holz",
    "is_subscribed": true,
    "recipes": [
        {
            "id": 22,
            "name": "werk",
            "image": null,
            "cooking_time": 59
        },
        {
            "id": 21,
            "name": "Anntrekottt",
            "image": null,
            "cooking_time": 59
        },
        {
            "id": 20,
            "name": "LollyBoom",
            "image": null,
            "cooking_time": 191
        }
    ],
    "recipes_count": 3
}
```
