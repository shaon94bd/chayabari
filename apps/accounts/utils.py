import re
import secrets

from django.utils.text import slugify

WORDS = (
    "brush canvas ochre umber sienna indigo cobalt easel fresco gesso charcoal pastel "
    "sketch palette amber jamun kadam shapla bokul shimul river monsoon lotus tiger"
).split()


def generate_password():
    """Readable but strong enough temporary password, e.g. "cobalt-4821-lotus"."""
    return f"{secrets.choice(WORDS)}-{secrets.randbelow(9000) + 1000}-{secrets.choice(WORDS)}"


def unique_username(base, model):
    base = re.sub(r"[^a-z0-9_.]", "", slugify(base).replace("-", "_"))[:24] or "artist"
    candidate, i = base, 2
    while model.objects.filter(username__iexact=candidate).exists():
        candidate, i = f"{base}{i}", i + 1
    return candidate
