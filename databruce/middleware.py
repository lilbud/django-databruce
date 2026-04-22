from django.shortcuts import redirect


class CleanQueryStringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
