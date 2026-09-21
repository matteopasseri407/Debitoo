from django.urls import include, path


urlpatterns = [
    path("api/", include("customers.urls")),
    path("api/", include("pratiche.urls")),
]
