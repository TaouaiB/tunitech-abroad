import fitz
from apps.cvs.models import CVUpload

class CVTextExtractionService:
    @classmethod
    def extract_text(cls, cv_upload: CVUpload) -> dict:
        try:
            return cls._do_extract(fitz.open(stream=cv_upload.file.read(), filetype="pdf"))
        except Exception as e:
            return cls._error_result(e)

    @classmethod
    def extract_from_path(cls, path: str) -> dict:
        try:
            return cls._do_extract(fitz.open(path))
        except Exception as e:
            return cls._error_result(e)

    @classmethod
    def _do_extract(cls, doc) -> dict:
        text_blocks = []
        for page in doc:
            text_blocks.append(page.get_text())

        raw_text = "\n".join(text_blocks).strip()
        doc.close()

        if len(raw_text) < 50:
            return {
                'success': False,
                'status': 'too_little_text',
                'raw_text': raw_text,
                'error': 'Text extracted is too short.'
            }

        return {
            'success': True,
            'status': 'success',
            'raw_text': raw_text,
        }

    @classmethod
    def _error_result(cls, e: Exception) -> dict:
        return {
            'success': False,
            'status': 'failed',
            'raw_text': '',
            'error': str(e)
        }
