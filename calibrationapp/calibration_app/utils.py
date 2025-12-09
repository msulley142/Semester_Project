from django.utils.html import strip_tags

# Utility function to sanitize text inputs
def sanitize_text(value):

    if value is None:
        return None
    if isinstance(value, str):
        return strip_tags(value).strip()
    return value


def sanitize_choice(value, allowed_values):
   
    if value is None:
        return None
    cleaned = sanitize_text(value)
    if cleaned is None:
        return None
    return cleaned if cleaned in allowed_values else None


def sanitize_int(value):
  
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None
