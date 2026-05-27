"""
Test suite for Video Converter Tool.
"""

import pytest
import os
import subprocess
import tempfile
from pathlib import Path


class TestVideoConverter:
    """Test cases for the VideoConverter class."""
    
    @pytest.fixture
    def test_video(self, tmp_path):
        """Create a test video file using ffmpeg."""
        video_path = tmp_path / "test_input.mp4"
        cmd = [
            'ffmpeg', '-f', 'lavfi',
            '-i', 'color=c=red:s=160x120:d=2',
            '-c:v', 'libx264', '-t', '2', '-y',
            str(video_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return str(video_path)
    
    def test_help_command(self):
        """Test --help command returns successfully."""
        result = subprocess.run(
            ['python', 'main.py', '--help'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode == 0
        assert 'Video Converter Tool' in result.stdout
        assert '--engines' in result.stdout
        assert '--info' in result.stdout
    
    def test_engines_command(self):
        """Test --engines command lists available engines."""
        result = subprocess.run(
            ['python', 'main.py', '--engines'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode == 0
        assert 'Available Conversion Engines' in result.stdout
        assert 'ffmpeg' in result.stdout
    
    def test_info_command(self, test_video):
        """Test --info command shows video information."""
        result = subprocess.run(
            ['python', 'main.py', '--info', test_video],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode == 0
        assert 'Video Information' in result.stdout
        assert test_video in result.stdout
    
    def test_info_nonexistent_file(self):
        """Test --info command with nonexistent file."""
        result = subprocess.run(
            ['python', 'main.py', '--info', '/nonexistent/video.mp4'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode != 0 or 'Error' in result.stdout
    
    def test_convert_same_format(self, test_video, tmp_path):
        """Test conversion with same format adds suffix."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Copy test video to output dir to avoid conflicts
        import shutil
        input_video = output_dir / "test_input.mp4"
        shutil.copy(test_video, input_video)
        
        result = subprocess.run(
            ['python', 'main.py', str(input_video), '--output-format', 'mp4', '--quality', '28'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode == 0
        assert 'Conversion successful' in result.stdout
        assert '_q28' in result.stdout or 'converted' in result.stdout.lower()
    
    def test_convert_different_format(self, test_video, tmp_path):
        """Test conversion to different format."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        import shutil
        input_video = output_dir / "test_input.mp4"
        shutil.copy(test_video, input_video)
        
        output_video = output_dir / "test_output.webm"
        
        result = subprocess.run(
            ['python', 'main.py', str(input_video), '-o', str(output_video)],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode == 0
        assert 'Conversion successful' in result.stdout
        assert os.path.exists(output_video)
    
    def test_convert_with_quality_preset(self, test_video, tmp_path):
        """Test conversion with quality presets."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        import shutil
        input_video = output_dir / "test_input.mp4"
        shutil.copy(test_video, input_video)
        
        for quality in ['14', '28', '72']:
            result = subprocess.run(
                ['python', 'main.py', str(input_video), '--output-format', 'mp4', '--quality', quality],
                capture_output=True,
                text=True,
                cwd='/workspace'
            )
            assert result.returncode == 0
            assert 'Conversion successful' in result.stdout
    
    def test_convert_nonexistent_input(self):
        """Test conversion with nonexistent input file."""
        result = subprocess.run(
            ['python', 'main.py', '/nonexistent/video.mp4', '--output-format', 'mp4'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        assert result.returncode != 0
        # Error message is in stderr (lowercase 'error')
        assert 'error' in result.stderr.lower() or 'Error' in result.stdout


class TestFFmpegAvailability:
    """Test FFmpeg availability."""
    
    def test_ffmpeg_installed(self):
        """Verify ffmpeg is installed and working."""
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'ffmpeg' in result.stdout.lower()
    
    def test_ffprobe_installed(self):
        """Verify ffprobe is installed and working."""
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'ffprobe' in result.stdout.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
