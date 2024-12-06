from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0

@register.filter
def clp(value):
    try:
        return f"${value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value
