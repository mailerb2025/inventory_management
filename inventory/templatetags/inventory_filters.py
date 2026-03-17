from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except:
        return 0

@register.filter
def divide(value, arg):
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except:
        return 0

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except:
        return 0

@register.filter
def currency(value):
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except:
        return None