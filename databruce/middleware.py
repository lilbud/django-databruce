from typing import Any

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers


class CleanQueryStringMiddleware:
  def __init__(self, get_response) -> None:
    self.get_response = get_response

  def __call__(self, request) -> HttpResponseRedirect | Any:
    # Only check GET requests with parameters
    if request.GET:
      has_quotes = False
      clean_get = request.GET.copy()

      for key, value in clean_get.items():
        if isinstance(value, str) and "'" in value:
          clean_get[key] = value.replace("'", "")
          has_quotes = True

      # If quotes were found, redirect to the clean URL
      if has_quotes:
        query_string = clean_get.urlencode()
        return redirect(f"{request.path}?{query_string}")

    return self.get_response(request)


class APINoCacheMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    response = self.get_response(request)

    # Adjust the path check if your API uses a different prefix or subdomain
    if request.path.startswith("/api/") and not response.has_header("Cache-Control"):
      add_never_cache_headers(response)

    return response
