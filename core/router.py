"""Router per selezionare l'engine appropriato in base al tipo di file."""

from pathlib import Path
from typing import Optional, Dict, Any, List
from .ffmpeg_engine import FFmpegEngine
from .pillow_engine import PillowEngine
from .pdf_engine import PDFEngine


class EngineRouter:
    """Router che seleziona l'engine appropriato per la conversione."""

    def __init__(self):
        self.engines = [
            FFmpegEngine(),
            PillowEngine(),
            PDFEngine()
        ]

    def get_engine(self, file_path: Path) -> Optional[Any]:
        """
        Trova l'engine appropriato per un dato file.
        
        Args:
            file_path: Percorso del file da elaborare
            
        Returns:
            L'engine appropriato o None se nessun engine è disponibile
        """
        for engine in self.engines:
            if engine.can_handle(file_path):
                return engine
        return None

    def get_supported_extensions(self) -> set:
        """Restituisce tutte le estensioni supportate."""
        extensions = set()
        for engine in self.engines:
            extensions.update(engine.SUPPORTED_EXTENSIONS)
        return extensions

    def convert(self, input_path: Path, output_path: Path,
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converte un file usando l'engine appropriato.
        
        Args:
            input_path: Percorso del file di input
            output_path: Percorso del file di output
            options: Opzioni specifiche per l'engine
            
        Returns:
            Dict con il risultato della conversione
        """
        engine = self.get_engine(input_path)
        
        if engine is None:
            return {
                'success': False,
                'message': f'Nessun engine disponibile per il file: {input_path.name}',
                'error': 'Unsupported format'
            }
        
        return engine.convert(input_path, output_path, options)

    def batch_convert(self, files: List[Path], output_dir: Path,
                      options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Converte più file in batch.
        
        Args:
            files: Lista di file da convertire
            output_dir: Directory di output
            options: Opzioni per la conversione
            
        Returns:
            Lista di risultati per ogni file
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            # Genera nome output
            output_name = file_path.stem  # Nome senza estensione
            output_path = output_dir / output_name
            
            result = self.convert(file_path, output_path, options)
            result['input_file'] = str(file_path)
            results.append(result)
        
        return results
