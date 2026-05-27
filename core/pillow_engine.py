"""Pillow engine for image conversion."""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from PIL import Image


class PillowEngine:
    """Engine per la conversione di immagini usando Pillow."""

    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', 
                            '.webp', '.ico', '.psd', '.raw'}
    
    OUTPUT_FORMATS = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.gif': 'GIF',
        '.bmp': 'BMP',
        '.tiff': 'TIFF',
        '.webp': 'WEBP',
        '.ico': 'ICO',
        '.pdf': 'PDF'
    }

    def __init__(self):
        pass

    def can_handle(self, file_path: Path) -> bool:
        """Verifica se questo engine può gestire il file."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, input_path: Path, output_path: Path,
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converte un'immagine.
        
        Args:
            input_path: Percorso del file di input
            output_path: Percorso del file di output
            options: Dizionario con opzioni come:
                - quality: 1-100 per JPEG/WEBP (default: 85)
                - resize: tuple (width, height) o None
                - format: formato output specifico
                - optimize: True/False per ottimizzazione (default: True)
                - grayscale: True/False per scala di grigi (default: False)
        
        Returns:
            Dict con status, message e eventuali dettagli
        """
        options = options or {}
        
        try:
            # Apri l'immagine
            with Image.open(input_path) as img:
                # Converti in RGB se necessario (per JPEG)
                output_ext = output_path.suffix.lower()
                
                # Gestione modalità colore
                if output_ext in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'P'):
                    # Crea sfondo bianco per trasparenze
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = background
                elif options.get('grayscale', False):
                    img = img.convert('L')
                elif output_ext in ['.jpg', '.jpeg']:
                    img = img.convert('RGB')
                
                # Resize
                resize = options.get('resize')
                if resize:
                    width, height = resize
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Determina il formato di output
                output_format = options.get('format') or self.OUTPUT_FORMATS.get(output_ext, None)
                if not output_format:
                    output_format = img.format or 'PNG'
                
                # Qualità e ottimizzazione
                save_kwargs = {}
                if output_format in ('JPEG', 'WEBP'):
                    save_kwargs['quality'] = options.get('quality', 85)
                    save_kwargs['optimize'] = options.get('optimize', True)
                elif output_format == 'PNG':
                    save_kwargs['optimize'] = options.get('optimize', True)
                
                # Salva l'immagine
                img.save(output_path, format=output_format, **save_kwargs)
            
            return {
                'success': True,
                'message': f'Conversione completata: {output_path.name}',
                'output_path': str(output_path),
                'details': f'Formato: {output_format}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Errore nella conversione immagine: {str(e)}',
                'error': str(e)
            }
