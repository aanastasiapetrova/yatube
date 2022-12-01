from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def permission_denied_view(request, exception):
    return render(request, 'core/403csrf.html', {'path': request.path},
                  status=403)


def internal_server_error(request, exception):
    return render(request, 'core/500.html', {'path': request.path}, status=500)
