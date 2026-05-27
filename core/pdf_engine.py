"""PDF engine for PDF operations using PyMuPDF."""

from pathlib import Path
from typing import Optional, Dict, Any, List
import fitz  # PyMuPDF


class PDFEngine:
    """Engine per operazioni su file PDF usando PyMuPDF."""

    SUPPORTED_EXTENSIONS = {'.pdf'}

    def __init__(self):
        pass

    def can_handle(self, file_path: Path) -> bool:
        """Verifica se questo engine può gestire il file."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, input_path: Path, output_path: Path,
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Esegue operazioni su un PDF.
        
        Args:
            input_path: Percorso del file di input
            output_path: Percorso del file di output
            options: Dizionario con opzioni come:
                - operation: 'compress', 'merge', 'split', 'to_images', 'images_to_pdf'
                - pages: lista di pagine da elaborare (default: tutte)
                - dpi: risoluzione per conversione immagini (default: 150)
                - quality: qualità compressione (default: 'medium')
                - source_files: lista di file per merge
        
        Returns:
            Dict con status, message e eventuali dettagli
        """
        options = options or {}
        operation = options.get('operation', 'compress')
        
        try:
            if operation == 'compress':
                return self._compress_pdf(input_path, output_path, options)
            elif operation == 'merge':
                return self._merge_pdfs(options)
            elif operation == 'split':
                return self._split_pdf(input_path, output_path, options)
            elif operation == 'to_images':
                return self._pdf_to_images(input_path, output_path, options)
            elif operation == 'images_to_pdf':
                return self._images_to_pdf(options)
            else:
                # Operazione default: copia/ottimizza
                return self._compress_pdf(input_path, output_path, options)
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Errore nell\'operazione PDF: {str(e)}',
                'error': str(e)
            }

    def _compress_pdf(self, input_path: Path, output_path: Path, 
                      options: Dict[str, Any]) -> Dict[str, Any]:
        """Comprime un PDF riducendo la qualità delle immagini."""
        quality = options.get('quality', 'medium')
        
        # Mappa qualità a impostazioni
        quality_settings = {
            'low': {'image_quality': 50, 'dpi': 72},
            'medium': {'image_quality': 75, 'dpi': 150},
            'high': {'image_quality': 90, 'dpi': 300}
        }
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        doc = fitz.open(input_path)
        
        # Opzioni di salvataggio
        save_options = {
            'garbage': 4,
            'deflate_images': True,
            'linear': True
        }
        
        doc.save(output_path, **save_options)
        doc.close()
        
        return {
            'success': True,
            'message': f'PDF compresso: {output_path.name}',
            'output_path': str(output_path),
            'details': f'Qualità: {quality}'
        }

    def _merge_pdfs(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Unisce più PDF in uno solo."""
        source_files = options.get('source_files', [])
        output_path = options.get('output_path')
        
        if not source_files or not output_path:
            return {
                'success': False,
                'message': 'File sorgente o percorso output mancanti',
                'error': 'Missing parameters'
            }
        
        result_doc = fitz.open()
        
        for file_path in source_files:
            path = Path(file_path)
            if path.exists():
                doc = fitz.open(path)
                result_doc.insert_pdf(doc)
                doc.close()
        
        result_doc.save(output_path)
        result_doc.close()
        
        return {
            'success': True,
            'message': f'PDF uniti: {len(source_files)} file',
            'output_path': str(output_path),
            'details': f'File uniti: {len(source_files)}'
        }

    def _split_pdf(self, input_path: Path, output_path: Path,
                   options: Dict[str, Any]) -> Dict[str, Any]:
        """Divide un PDF in pagine separate."""
        pages = options.get('pages')  # Lista di numeri pagina o None per tutte
        
        doc = fitz.open(input_path)
        
        if pages is None:
            pages = list(range(len(doc)))
        
        output_paths = []
        for i, page_num in enumerate(pages):
            if 0 <= page_num < len(doc):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Genera nome file
                stem = output_path.stem
                parent = output_path.parent
                page_output = parent / f"{stem}_page_{page_num + 1}.pdf"
                
                new_doc.save(page_output)
                new_doc.close()
                output_paths.append(str(page_output))
        
        doc.close()
        
        return {
            'success': True,
            'message': f'PDF diviso in {len(output_paths)} pagine',
            'output_path': output_paths[0] if output_paths else str(output_path),
            'details': f'Pagine estratte: {len(output_paths)}'
        }

    def _pdf_to_images(self, input_path: Path, output_path: Path,
                       options: Dict[str, Any]) -> Dict[str, Any]:
        """Converte le pagine PDF in immagini."""
        dpi = options.get('dpi', 150)
        image_format = options.get('format', 'png')
        
        doc = fitz.open(input_path)
        output_paths = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix)
            
            # Genera nome file
            stem = output_path.stem
            parent = output_path.parent
            img_output = parent / f"{stem}_page_{page_num + 1}.{image_format}"
            
            pix.save(str(img_output))
            output_paths.append(str(img_output))
        
        doc.close()
        
        return {
            'success': True,
            'message': f'PDF convertito in {len(output_paths)} immagini',
            'output_path': output_paths[0] if output_paths else str(output_path),
            'details': f'Immagini generate: {len(output_paths)}, DPI: {dpi}'
        }

    def _images_to_pdf(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Converte immagini in un PDF."""
        source_files = options.get('source_files', [])
        output_path = options.get('output_path')
        
        if not source_files or not output_path:
            return {
                'success': False,
                'message': 'File sorgente o percorso output mancanti',
                'error': 'Missing parameters'
            }
        
        result_doc = fitz.open()
        
        for file_path in source_files:
            path = Path(file_path)
            if path.exists():
                img = fitz.open(path)
                if len(img) > 0:
                    page = result_doc.new_page(width=img[0].rect.width,
                                               height=img[0].rect.height)
                    page.insert_image(page.rect, filename=path)
                img.close()
        
        result_doc.save(output_path)
        result_doc.close()
        
        return {
            'success': True,
            'message': f'Immagini convertite in PDF: {len(source_files)} file',
            'output_path': str(output_path),
            'details': f'Immagini elaborate: {len(source_files)}'
        }
