from django.contrib import admin #type:ignore
from django.urls import path, include #type:ignore

urlpatterns = [
    path('admin/', admin.site.urls),
    path('convert/pdf-to-word/', include('pdf_to_word.urls')),
    path('convert/pdf-to-excel/', include('pdf_to_excel.urls')),
]