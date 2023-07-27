from django.core.exceptions import ValidationError


def time_validate(value):
    if not (value >= 1):
        raise ValidationError(
            'Время приготовления блюда не может быть меньше 1 минуты!'
        )
    return value


def amount_validate(value):
    if not (value >= 1):
        raise ValidationError(
            'Количество продукта не может быть меньше 1!'
        )
    return value
