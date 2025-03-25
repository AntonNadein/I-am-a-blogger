#
#
# class CachedViewMixin:
#     """Примесь для кэширования представлений с общими методами и переменными."""
#
#     cache_timeout = 60 * 30  # Время кеширования в секундах
#     cache_key = None  # Имя ключа кеша
#
#     def get_cache_key(self):
#         """Возвращает ключ для кэширования, основанный на имени модели."""
#         if self.cache_key is None:
#             return self.model.__name__.lower() + "_cache"
#         return self.cache_key
#
#     def cache_queryset(self, queryset):
#         """Кэширует переданный queryset с использованием заданного ключа."""
#         cache.set(self.get_cache_key(), queryset, self.cache_timeout)
#
#     def get_cached_queryset(self):
#         """Пытается получить queryset из кэша, возвращает None, если не удается."""
#         return cache.get(self.get_cache_key())
