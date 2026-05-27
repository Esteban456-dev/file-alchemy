#!/usr/bin/env python3
"""
Video Converter Tool - A command-line tool for converting videos using FFmpeg.
Supports multiple engines and output formats.
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class VideoConverter:
    """Main class for handling video conversion operations."""
    
    SUPPORTED_ENGINES = ['ffmpeg', 'libav']
    SUPPORTED_FORMATS = ['mp4', 'avi', 'mkv', 'mov', 'webm', 'gif', 'mp3', 'aac', 'wav']
    QUALITY_PRESETS = {
        '14': {'video_bitrate': '600k', 'audio_bitrate': '64k', 'resolution': '256x144'},
        '28': {'video_bitrate': '1000k', 'audio_bitrate': '96k', 'resolution': '426x240'},
        '72': {'video_bitrate': '2500k', 'audio_bitrate': '128k', 'resolution': '1280x720'},
        '1080': {'video_bitrate': '5000k', 'audio_bitrate': '192k', 'resolution': '1920x1080'},
    }
    
    def __init__(self, engine: str = 'ffmpeg'):
        """Initialize the converter with specified engine."""
        self.engine = engine
        self._check_engine()
    
    def _check_engine(self) -> None:
        """Check if the specified engine is available."""
        try:
            result = subprocess.run(
                [self.engine, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"Engine {self.engine} is not working properly")
        except FileNotFoundError:
            raise RuntimeError(f"Engine '{self.engine}' not found. Please install it.")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Engine '{self.engine}' check timed out")
    
    @staticmethod
    def list_engines() -> List[Dict[str, Any]]:
        """List all available engines and their status."""
        engines = []
        for engine in VideoConverter.SUPPORTED_ENGINES:
            try:
                result = subprocess.run(
                    [engine, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                version_line = result.stdout.split('\n')[0] if result.stdout else 'Unknown'
                engines.append({
                    'name': engine,
                    'available': True,
                    'version': version_line
                })
            except (FileNotFoundError, subprocess.TimeoutExpired):
                engines.append({
                    'name': engine,
                    'available': False,
                    'version': 'Not installed'
                })
        return engines
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get detailed information about a video file."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cmd = [
            self.engine, '-i', video_path,
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # ffprobe is typically used for info, fallback to parsing ffmpeg output
            if result.returncode != 0:
                # Try with ffprobe
                probe_cmd = [
                    'ffprobe', '-i', video_path,
                    '-print_format', 'json',
                    '-show_streams',
                    '-show_format',
                    '-'
                ]
                result = subprocess.run(
                    probe_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_video_info(data, video_path)
            else:
                # Fallback: basic info from ffmpeg stderr
                return self._parse_basic_info(video_path)
                
        except json.JSONDecodeError:
            return self._parse_basic_info(video_path)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Getting video info timed out")
    
    def _parse_video_info(self, data: Dict, video_path: str) -> Dict[str, Any]:
        """Parse ffprobe JSON output."""
        info = {
            'file': video_path,
            'size': os.path.getsize(video_path),
            'format': {},
            'streams': []
        }
        
        if 'format' in data:
            fmt = data['format']
            info['format'] = {
                'duration': float(fmt.get('duration', 0)),
                'bitrate': fmt.get('bit_rate', 'N/A'),
                'format_name': fmt.get('format_name', 'N/A'),
                'format_long_name': fmt.get('format_long_name', 'N/A'),
            }
        
        if 'streams' in data:
            for stream in data['streams']:
                stream_info = {
                    'index': stream.get('index'),
                    'codec_type': stream.get('codec_type'),
                    'codec_name': stream.get('codec_name'),
                }
                if stream.get('codec_type') == 'video':
                    stream_info.update({
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'fps': stream.get('r_frame_rate', 'N/A'),
                        'pix_fmt': stream.get('pix_fmt'),
                    })
                elif stream.get('codec_type') == 'audio':
                    stream_info.update({
                        'sample_rate': stream.get('sample_rate'),
                        'channels': stream.get('channels'),
                        'channel_layout': stream.get('channel_layout'),
                    })
                info['streams'].append(stream_info)
        
        return info
    
    def _parse_basic_info(self, video_path: str) -> Dict[str, Any]:
        """Parse basic info when ffprobe is not available."""
        cmd = [self.engine, '-i', video_path]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            # ffmpeg outputs info to stderr
            output = result.stderr
            
            info = {
                'file': video_path,
                'size': os.path.getsize(video_path),
                'raw_info': output
            }
            return info
        except Exception as e:
            return {
                'file': video_path,
                'size': os.path.getsize(video_path),
                'error': str(e)
            }
    
    def convert(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        output_format: Optional[str] = None,
        quality: Optional[str] = None,
        verbose: bool = False
    ) -> str:
        """Convert video to specified format and quality."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        input_file = Path(input_path)
        input_ext = input_file.suffix.lstrip('.').lower()
        
        # Determine output path
        if output_path is None:
            ext = output_format or input_ext
            # If same format, add quality suffix or '_converted' to avoid overwriting
            if ext == input_ext:
                suffix = f"_q{quality}" if quality else "_converted"
                output_path = str(input_file.with_stem(f"{input_file.stem}{suffix}"))
            else:
                output_path = str(input_file.with_suffix(f'.{ext}'))
        elif output_format:
            output_path = Path(output_path).with_suffix(f'.{output_format}')
        
        # Build ffmpeg command
        cmd = [self.engine, '-y', '-i', input_path]
        
        # Apply quality settings
        if quality and quality in self.QUALITY_PRESETS:
            preset = self.QUALITY_PRESETS[quality]
            cmd.extend([
                '-vf', f"scale={preset['resolution']}",
                '-b:v', preset['video_bitrate'],
                '-b:a', preset['audio_bitrate'],
            ])
        elif quality:
            # Custom CRF value
            try:
                crf = int(quality)
                if 0 <= crf <= 51:
                    cmd.extend(['-crf', str(crf)])
            except ValueError:
                pass
        
        # Set output format codec based on extension
        ext = Path(output_path).suffix.lstrip('.').lower()
        if ext == 'mp4':
            cmd.extend(['-c:v', 'libx264', '-c:a', 'aac'])
        elif ext == 'webm':
            cmd.extend(['-c:v', 'libvpx-vp9', '-c:a', 'libopus'])
        elif ext == 'gif':
            cmd.extend(['-vf', 'fps=10,scale=320:-1:flags=lanczos'])
        elif ext in ['mp3', 'aac', 'wav']:
            cmd = [self.engine, '-y', '-i', input_path]
            if ext == 'mp3':
                cmd.extend(['-vn', '-c:a', 'libmp3lame'])
            elif ext == 'aac':
                cmd.extend(['-vn', '-c:a', 'aac'])
            elif ext == 'wav':
                cmd.extend(['-vn', '-c:a', 'pcm_s16le'])
        
        cmd.append(str(output_path))
        
        if verbose:
            print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout for conversion
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise RuntimeError(f"Conversion failed: {error_msg}")
            
            if not os.path.exists(output_path):
                raise RuntimeError("Output file was not created")
            
            return str(output_path)
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Video Converter Tool - Convert videos using FFmpeg',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4 --output-format mp4 --quality 72
  %(prog)s input.mov -o output.avi
  %(prog)s --info video.mp4
  %(prog)s --engines
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input video file path')
    parser.add_argument('--engines', action='store_true', 
                       help='List available conversion engines')
    parser.add_argument('--info', metavar='FILE', 
                       help='Show information about a video file')
    parser.add_argument('-o', '--output', metavar='PATH',
                       help='Output file path')
    parser.add_argument('--output-format', metavar='FORMAT',
                       choices=VideoConverter.SUPPORTED_FORMATS,
                       help='Output format (mp4, avi, mkv, mov, webm, gif, mp3, aac, wav)')
    parser.add_argument('--quality', metavar='QUALITY',
                       help='Quality preset (14, 28, 72, 1080) or CRF value (0-51)')
    parser.add_argument('--engine', default='ffmpeg',
                       help='Conversion engine to use (default: ffmpeg)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Handle --engines flag
    if args.engines:
        print("Available Conversion Engines:")
        print("-" * 50)
        engines = VideoConverter.list_engines()
        for engine in engines:
            status = "✓ Available" if engine['available'] else "✗ Not available"
            print(f"  {engine['name']}: {status}")
            if engine['available']:
                print(f"    Version: {engine['version']}")
        return 0
    
    # Handle --info flag
    if args.info:
        try:
            converter = VideoConverter(engine=args.engine)
            info = converter.get_video_info(args.info)
            
            print(f"\nVideo Information:")
            print("=" * 50)
            print(f"File: {info['file']}")
            print(f"Size: {info['size']} bytes ({info['size'] / 1024 / 1024:.2f} MB)")
            
            if 'format' in info and info['format']:
                fmt = info['format']
                print(f"\nFormat:")
                print(f"  Duration: {fmt.get('duration', 0):.2f} seconds")
                print(f"  Bitrate: {fmt.get('bitrate', 'N/A')}")
                print(f"  Format: {fmt.get('format_name', 'N/A')}")
            
            if 'streams' in info and info['streams']:
                print(f"\nStreams:")
                for stream in info['streams']:
                    print(f"  Stream #{stream.get('index')}: {stream.get('codec_type')}")
                    print(f"    Codec: {stream.get('codec_name')}")
                    if stream.get('codec_type') == 'video':
                        print(f"    Resolution: {stream.get('width')}x{stream.get('height')}")
                        print(f"    FPS: {stream.get('fps')}")
                    elif stream.get('codec_type') == 'audio':
                        print(f"    Sample Rate: {stream.get('sample_rate')} Hz")
                        print(f"    Channels: {stream.get('channels')}")
            print()
            return 0
        except Exception as e:
            print(f"Error getting video info: {e}", file=sys.stderr)
            return 1
    
    # Handle conversion
    if args.input:
        try:
            converter = VideoConverter(engine=args.engine)
            
            output = converter.convert(
                input_path=args.input,
                output_path=args.output,
                output_format=args.output_format,
                quality=args.quality,
                verbose=args.verbose
            )
            
            print(f"Conversion successful!")
            print(f"Output file: {output}")
            print(f"Output size: {os.path.getsize(output)} bytes ({os.path.getsize(output) / 1024 / 1024:.2f} MB)")
            return 0
            
        except Exception as e:
            print(f"Error during conversion: {e}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
