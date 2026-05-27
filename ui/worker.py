"""Worker per l'elaborazione dei file in background."""

from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import os

# Aggiungi il percorso del progetto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.router import EngineRouter


class ConversionWorker(QThread):
    """Worker che esegue la conversione dei file in un thread separato."""

    # Segnali per comunicare con la UI
    progress = pyqtSignal(int, str)  # percent, message
    file_complete = pyqtSignal(str, bool, str)  # filename, success, message
    finished = pyqtSignal(list)  # lista di tutti i risultati
    error = pyqtSignal(str)  # messaggio di errore

    def __init__(self, files: List[str], output_dir: str, options: Dict[str, Any] = None):
        super().__init__()
        self.files = [Path(f) for f in files]
        self.output_dir = Path(output_dir)
        self.options = options or {}
        self.results = []
        self.router = EngineRouter()

    def run(self):
        """Esegue la conversione dei file."""
        try:
            # Crea la directory di output se non esiste
            self.output_dir.mkdir(parents=True, exist_ok=True)

            total_files = len(self.files)
            
            for index, file_path in enumerate(self.files):
                if not file_path.exists():
                    self.file_complete.emit(str(file_path.name), False, "File non trovato")
                    self.results.append({
                        'file': str(file_path),
                        'success': False,
                        'message': 'File non trovato'
                    })
                    continue

                # Aggiorna progresso
                progress_percent = int((index / total_files) * 100)
                self.progress.emit(progress_percent, f"Elaborazione: {file_path.name}")

                # Esegui la conversione
                result = self._convert_file(file_path)
                self.results.append(result)

                # Emetti segnale di completamento file
                self.file_complete.emit(
                    file_path.name,
                    result['success'],
                    result['message']
                )

            # Completamento di tutti i file
            final_progress = 100
            self.progress.emit(final_progress, "Conversione completata")
            self.finished.emit(self.results)

        except Exception as e:
            self.error.emit(f"Errore durante la conversione: {str(e)}")
            self.finished.emit(self.results)

    def _convert_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Converte un singolo file usando l'engine appropriato.
        
        Args:
            file_path: Percorso del file da convertire
            
        Returns:
            Dict con il risultato della conversione
        """
        # Determina il percorso di output
        output_ext = self.options.get('output_format', file_path.suffix)
        output_name = f"{file_path.stem}{output_ext}"
        output_path = self.output_dir / output_name

        # Prepara le opzioni specifiche per l'engine
        engine_options = self._map_ui_options_to_engine(file_path, output_ext)

        # Usa il router per trovare l'engine e convertire
        result = self.router.convert(file_path, output_path, engine_options)
        
        # Aggiungi informazioni aggiuntive al risultato
        result['input_file'] = str(file_path)
        result['output_file'] = str(output_path) if result['success'] else None

        return result

    def _map_ui_options_to_engine(self, file_path: Path, output_ext: str) -> Dict[str, Any]:
        """
        Mappa le opzioni della UI ai parametri degli engine.
        
        Args:
            file_path: Percorso del file di input
            output_ext: Estensione del file di output
            
        Returns:
            Dizionario con le opzioni mappate per l'engine
        """
        engine_options = {}
        suffix = file_path.suffix.lower()

        # Opzioni comuni per immagini (Pillow)
        if suffix in PillowEngine.SUPPORTED_EXTENSIONS if 'PillowEngine' in globals() else suffix in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}:
            # Qualità immagine
            quality_map = {
                'low': 60,
                'medium': 85,
                'high': 95
            }
            engine_options['quality'] = quality_map.get(
                self.options.get('image_quality', 'medium'), 
                85
            )
            
            # Resize
            if self.options.get('resize_enabled', False):
                width = self.options.get('resize_width', 1920)
                height = self.options.get('resize_height', 1080)
                engine_options['resize'] = (width, height)
            
            # Scala di grigi
            if self.options.get('grayscale', False):
                engine_options['grayscale'] = True
            
            # Ottimizzazione
            engine_options['optimize'] = self.options.get('optimize_images', True)

        # Opzioni per video (FFmpeg)
        elif suffix in FFmpegEngine.SUPPORTED_EXTENSIONS if 'FFmpegEngine' in globals() else suffix in {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.mp3', '.wav', '.aac'}:
            # Qualità video
            quality_map = {
                'low': 'low',
                'medium': 'medium',
                'high': 'high',
                'ultra': 'ultra'
            }
            engine_options['quality'] = quality_map.get(
                self.options.get('video_quality', 'medium'),
                'medium'
            )
            
            # Codec
            engine_options['video_codec'] = self.options.get('video_codec', 'libx264')
            engine_options['audio_codec'] = self.options.get('audio_codec', 'aac')
            
            # Resize video
            if self.options.get('resize_video_enabled', False):
                width = self.options.get('resize_video_width', 1920)
                height = self.options.get('resize_video_height', 1080)
                engine_options['resize'] = (width, height)
            
            # FPS
            fps = self.options.get('fps')
            if fps:
                engine_options['fps'] = fps
            
            # Bitrate audio
            engine_options['audio_bitrate'] = self.options.get('audio_bitrate', '128k')

        # Opzioni per PDF
        elif suffix == '.pdf':
            # Operazione PDF
            operation = self.options.get('pdf_operation', 'compress')
            engine_options['operation'] = operation
            
            # Qualità compressione
            engine_options['quality'] = self.options.get('pdf_quality', 'medium')
            
            # DPI per conversione immagini
            engine_options['dpi'] = self.options.get('pdf_dpi', 150)
            
            # Formato output immagini
            engine_options['format'] = self.options.get('pdf_image_format', 'png')

        return engine_options


# Import necessari per il mapping delle opzioni
from core.ffmpeg_engine import FFmpegEngine
from core.pillow_engine import PillowEngine
