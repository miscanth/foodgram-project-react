import csv

from django.core.management import BaseCommand

from recipes.models import Ingredient


MODELS = [Ingredient]

ALREDY_LOADED_ERROR_MESSAGE = """
If you need to reload the csv data from the CSV file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""


class Command(BaseCommand):
    help = 'Loads data from csv files'

    def handle(self, *args, **options):
        for Model in MODELS:
            if Model.objects.exists():
                print('category data already loaded...exiting.')
                print(ALREDY_LOADED_ERROR_MESSAGE)
                return
        print('Loading category data')
        handle_ingredients()


def handle_ingredients():
    with open(('data/ingredients.csv'), mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        for row in reader:
            object_dict = {
                key: value
                for key, value in zip(header, row)
            }
            Ingredient.objects.create(**object_dict)
