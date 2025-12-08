from django.utils.html import strip_tags

# Utility function to sanitize text inputs
def sanitize_text(value):

    if value is None:
        return None
    if isinstance(value, str):
        return strip_tags(value).strip()
    return value
