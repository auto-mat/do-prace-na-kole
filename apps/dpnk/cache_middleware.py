from django.utils.deprecation import MiddlewareMixin

from threading import local

_request_local = local()


class RequestCacheMiddleware(MiddlewareMixin):
    """Middleware to provide request-scoped caching via thread-local storage"""

    def process_request(self, request):
        # Clear any existing cache and store new request
        _request_local.request = request
        _request_local.cache = {}

    def process_response(self, request, response):
        # Clean up thread-local storage
        if hasattr(_request_local, "cache"):
            _request_local.cache.clear()
        if hasattr(_request_local, "request"):
            delattr(_request_local, "request")
        return response


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_request_local, "request", None)


def get_request_cache():
    """Get the current request cache"""
    return getattr(_request_local, "cache", {})
