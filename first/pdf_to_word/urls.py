from django.urls import path 
from .views import PdfToWordView

urlpatterns = [
    path('', PdfToWordView.as_view(), name='pdf_to_word'),
]