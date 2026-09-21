from django.urls import path

from pratiche.views import PraticaDetailView, PraticaListCreateView

urlpatterns = [
    # Endpoint principali in lingua italiana (aderenti alla specifica della prova)
    path("pratiche/", PraticaListCreateView.as_view(), name="pratica-list-create"),
    path("pratiche/<int:pk>/", PraticaDetailView.as_view(), name="pratica-detail"),
    path("pratiche/<int:pk>/stato/", PraticaDetailView.as_view(), name="pratica-status-update"),

    # Alias opzionali in lingua inglese per massima flessibilità di integrazione
    path("cases/", PraticaListCreateView.as_view(), name="case-list-create"),
    path("cases/<int:pk>/", PraticaDetailView.as_view(), name="case-detail"),
    path("cases/<int:pk>/status/", PraticaDetailView.as_view(), name="case-status-update"),
]
