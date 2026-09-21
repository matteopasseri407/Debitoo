"""
Gestore globale delle eccezioni per formattare gli errori in lingua italiana.
"""
from rest_framework.views import exception_handler


def italian_exception_handler(exc, context):
    """
    Intercetta le risposte di errore standard di Django REST Framework
    e assicura messaggi amichevoli e chiari in italiano.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Se c'è un messaggio 404 standard in inglese/generico, lo traduciamo
        if response.status_code == 404 and "detail" in response.data:
            if response.data["detail"] in ["Not found.", "Non trovato."]:
                response.data["detail"] = "Risorsa richiesta non trovata."

    return response
