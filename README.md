![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)  ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)  ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)  ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)  ![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)  ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)  ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)


# «Продуктовый помощник» - кулинарная социальная сеть
Деплой проекта Foodgram в **Docker контейнерах** 


## Описание и возможности проекта: 

Проект Foodgram - это приложение ***«Продуктовый помощник»***: сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 

Это полностью рабочий проект, который состоит из бэкенд-приложения на **Django** и фронтенд-приложения на **React**. 

API для Foodgram написан с использованием библиотеки **Django REST Framework**, используется **TokenAuthentication** для аутентификации, а также подключена библиотека **Djoser**.

Проект размещён в **Docker** контейнерах. В контейнере бэкенда настроен **WSGI-сервер Gunicorn**.
Автоматизация тестирования и деплоя проекта осуществлена с помощью **GitHub Actions**.


## Технологии

- Python 3.9
- Django 3.2.16
- Django REST framework 3.12.4
- PostgreSQL
- Docker
- Nginx
- Gunicorn
- GitHub Actions


## Локальный запуск проекта

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
    source venv/bin/activate
    ```
* Если у вас windows 
 
    ```
    source venv/scripts/activate
    ```
```
python3.9 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Задайте учётные данные БД в .env файле, используя .env.example (находится в корневой директории проекта):
```
POSTGRES_USER=логин
POSTGRES_PASSWORD=пароль
POSTGRES_DB=название БД
DB_HOST=название хоста
DB_PORT=5432
SECRET_KEY=django_settings_secret_key
ALLOWED_HOSTS=127.0.0.1, localhost
```

**Запустить Docker Compose с дефолтной конфигурацией (docker-compose.yml):**

* Выполнить сборку контейнеров: *sudo docker compose up -d --build* или в отдельном терминале *sudo docker compose up*

* Применить миграции: *sudo docker compose exec backend python manage.py migrate*

* Создать суперпользователя: *sudo docker compose exec backend python manage.py createsuperuser*

* Собрать файлы статики: *sudo docker compose exec backend python manage.py collectstatic*

* Скопировать файлы статики в /backend_static/static/ backend-контейнера: *sudo docker compose exec backend cp -r /app/collected_static/. /backend_static/static/*

* Для загрузки тестовых данных (списки ингредиентов): *sudo docker compose exec backend python manage.py load_csv_data*

* Перейти по адресу 127.0.0.1:8000


## Как открыть документацию:
Подробное описание ресурсов в документации после запуска проекта доступно по адресу: http://127.0.0.1:8000/api/docs/


## Настройка CI/CD

Деплой проекта на удалённый сервер настроен через CI/CD с помощью GitHub Actions, для этого создан workflow, в котором:

* проверяется код бэкенда в репозитории на соответствие PEP8;
* в случае успешного прохождения тестов образы должны обновляться на Docker Hub;
* обновляются образы на сервере и перезапускается приложение при помощи Docker Compose;
* выполняются команды для сборки статики в приложении бэкенда, переноса статики в volume; выполняются миграции;
* происходит уведомление в Telegram об успешном завершении деплоя.

Пример данного workflow сохранен в файле foodgram_workflow.yml в корневой директории проекта, при необходимости запуска перепишите содержимое файла в .github/workflows/main.yml.

Сохраните следующие переменные с необходимыми значениями в секретах GitHub Actions:

```
DOCKER_USERNAME - логин в Docker Hub
DOCKER_PASSWORD - пароль для Docker Hub
SSH_KEY - закрытый SSH-ключ для доступа к продакшен-серверу
SSH_PASSPHRASE - passphrase для этого ключа
USER - username для доступа к продакшен-серверу
HOST - адрес хоста для доступа к продакшен-серверу
TELEGRAM_TO - ID своего телеграм-аккаунта
TELEGRAM_TOKEN - токен Telegram-бота
```

Файл docker-compose.yml для локального запуска проекта и файл docker-compose.production.yml для запуска проекта на облачном сервере находятся в корневой директории проекта.

## Примеры запросов:

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


## Разработчик (исполнитель):
👩🏼‍💻 Юлия: https://github.com/miscanth