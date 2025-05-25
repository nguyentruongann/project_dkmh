from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Trả về dictionary[key] hoặc {} nếu không có key."""
    if dictionary:
        return dictionary.get(str(key), {})
    return {}
