from django.core.cache import cache


class CachedViewMixin:
    """Примесь для кэширования представлений с общими методами и переменными."""

    cache_timeout = 60 * 30  # Время кеширования в секундах
    cache_key = None  # Имя ключа кеша

    def _get_cache_key(self):
        """Возвращает ключ для кэширования, основанный на имени модели и пути."""
        if self.cache_key is None:
            name = self.model.__name__.lower() + self.request.path
            return name + "_cache"
        return self.cache_key

    def cache_queryset(self, queryset):
        """Кэширует переданный queryset с использованием заданного ключа."""
        cache.set(self._get_cache_key(), queryset, self.cache_timeout)

    def get_cached_queryset(self):
        """Пытается получить queryset из кэша, возвращает None, если не удается."""
        return cache.get(self._get_cache_key())

    def clear_cached(self):
        """Очищает кэш по ключу."""
        return cache.delete(self._get_cache_key())
