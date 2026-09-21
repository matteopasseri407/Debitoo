from django.urls import path

from pratiche.views import PraticaDetailView, PraticaListCreateView

urlpatterns = [
    path("pratiche/", PraticaListCreateView.as_view(), name="pratica-list-create"),
    path("pratiche/<int:pk>/", PraticaDetailView.as_view(), name="pratica-detail"),
]
