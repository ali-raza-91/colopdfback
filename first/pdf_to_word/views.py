import os
import uuid
import logging
from pathlib import Path
from django.http import FileResponse, JsonResponse #type:ignore
from django.views import View  #type:ignore
from django.conf import settings  #type:ignore
import magic  #type:ignore
from pdf2docx import Converter  #type:ignore

logger = logging.getLogger(__name__)

class PdfToWordView(View):
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        
        # Validate file
        validation_error = self._validate_file(file)
        if validation_error:
            return validation_error
        
        # Process conversion
        try:
            return self._convert_pdf_to_word(file)
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            return JsonResponse(
                {'error': 'Failed to process PDF'},
                status=500
            )
    
    def _validate_file(self, file):
        if file.size > self.MAX_FILE_SIZE:
            return JsonResponse(
                {'error': 'File too large. Max 50MB allowed'},
                status=400
            )
        
        try:
            mime = magic.Magic(mime=True)
            if mime.from_buffer(file.read(1024)) != 'application/pdf':
                return JsonResponse(
                    {'error': 'Only PDF files are supported'},
                    status=400
                )
            file.seek(0)
        except Exception as e:
            logger.warning(f"File validation failed: {str(e)}")
            return JsonResponse(
                {'error': 'Invalid file format'},
                status=400
            )
        return None
    
    def _convert_pdf_to_word(self, file):
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_pdf_to_word')
        os.makedirs(temp_dir, exist_ok=True)
        
        file_id = uuid.uuid4().hex
        pdf_path = os.path.join(temp_dir, f'{file_id}.pdf')
        docx_path = os.path.join(temp_dir, f'{file_id}.docx')
        
        try:
            # Save uploaded file
            with open(pdf_path, 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            
            # Convert
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            
            # Return response
            response = FileResponse(
                open(docx_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                filename=f"{Path(file.name).stem}.docx"
            )
            
            # Cleanup
            def cleanup():
                for path in [pdf_path, docx_path]:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception as e:
                        logger.error(f"Failed to cleanup {path}: {str(e)}")
            
            response.closed.connect(cleanup)
            
            return response
        except Exception as e:
            # Cleanup on failure
            for path in [pdf_path, docx_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass
            raise