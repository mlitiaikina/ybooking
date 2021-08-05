from slugify import slugify


def generate_username(first_name: str, last_name: str) -> str:
    return f'{slugify(first_name.lower()[0])}_{slugify(last_name.lower())}'