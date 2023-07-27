from django.core.exceptions import ValidationError


def check_username(value):
    if value.lower() == 'me':
        raise ValidationError(
            'Имя пользователя не может быть "Me, ME, me, mE'
        )
