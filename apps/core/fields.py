from rest_framework import serializers


class AbsoluteImageField(serializers.ImageField):
    """Returns a URL relative to the site root ("/media/...") so it works behind any host."""

    def to_representation(self, value):
        if not value:
            return None
        try:
            return value.url
        except ValueError:
            return None
