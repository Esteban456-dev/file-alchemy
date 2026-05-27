"""FFmpeg engine for video/audio conversion."""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


class FFmpegEngine:
    """Engine per la conversione di file video e audio usando FFmpeg."""

    SUPPORTED_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
                            '.mp3', '.wav', '.aac', '.flac', '.ogg'}

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        """Trova il percorso di ffmpeg nel sistema."""
        return 'ffmpeg'  # Assume ffmpeg è nel PATH

    def can_handle(self, file_path: Path) -> bool:
        """Verifica se questo engine può gestire il file."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def convert(self, input_path: Path, output_path: Path, 
                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Converte un file video/audio.
        
        Args:
            input_path: Percorso del file di input
            output_path: Percorso del file di output
            options: Dizionario con opzioni come:
                - quality: 'low', 'medium', 'high' (default: 'medium')
                - video_codec: codec video (default: 'libx264')
                - audio_codec: codec audio (default: 'aac')
                - resize: tuple (width, height) o None
                - fps: frame rate (default: originale)
                - audio_bitrate: bitrate audio (default: '128k')
        
        Returns:
            Dict con status, message e eventuali dettagli
        """
        options = options or {}
        
        # Costruisci il comando ffmpeg
        cmd = [self.ffmpeg_path, '-y', '-i', str(input_path)]
        
        # Gestione qualità
        quality = options.get('quality', 'medium')
        crf_map = {'low': 28, 'medium': 23, 'high': 18, 'ultra': 15}
        crf = crf_map.get(quality, 23)
        
        # Codec video
        video_codec = options.get('video_codec', 'libx264')
        if video_codec:
            cmd.extend(['-c:v', video_codec])
            if video_codec == 'libx264':
                cmd.extend(['-crf', str(crf)])
        
        # Codec audio
        audio_codec = options.get('audio_codec', 'aac')
        if audio_codec:
            cmd.extend(['-c:a', audio_codec])
            audio_bitrate = options.get('audio_bitrate', '128k')
            cmd.extend(['-b:a', audio_bitrate])
        
        # Resize
        resize = options.get('resize')
        if resize:
            width, height = resize
            scale_filter = f'scale={width}:{height}'
            cmd.extend(['-vf', scale_filter])
        
        # FPS
        fps = options.get('fps')
        if fps:
            cmd.extend(['-r', str(fps)])
        
        # Output path
        cmd.append(str(output_path))
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 ora timeout
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Conversione completata: {output_path.name}',
                    'output_path': str(output_path),
                    'details': result.stderr
                }
            else:
                return {
                    'success': False,
                    'message': f'Errore nella conversione: {result.stderr}',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Timeout durante la conversione',
                'error': 'TimeoutExpired'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'message': 'FFmpeg non trovato. Installare FFmpeg.',
                'error': 'FFmpeg not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Errore imprevisto: {str(e)}',
                'error': str(e)
            }
