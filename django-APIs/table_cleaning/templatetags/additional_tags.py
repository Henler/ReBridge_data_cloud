from django import template
from python_back_end.data_cleaning.cleaning_utils import GeneralStringFormatter

register = template.Library()


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def num_str_date_format(string):
    return GeneralStringFormatter.format(string)