"""
Tests for PillowEngine.
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import os

from core.engines.pillow import PillowEngine


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample PNG image for testing."""
    img_path = temp_dir / "sample.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path, 'PNG')
    return img_path


@pytest.fixture
def sample_rgba_image(temp_dir):
    """Create a sample RGBA PNG image for testing."""
    img_path = temp_dir / "sample_rgba.png"
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    img.save(img_path, 'PNG')
    return img_path


class TestPillowEngineSupports:
    """Test the supports method of PillowEngine."""

    def test_supports_png(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "image.png") is True

    def test_supports_jpg(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "image.jpg") is True

    def test_supports_jpeg(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "image.jpeg") is True

    def test_supports_webp(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "image.webp") is True

    def test_does_not_support_pdf(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "document.pdf") is False

    def test_does_not_support_mp4(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "video.mp4") is False

    def test_case_insensitive(self, temp_dir):
        engine = PillowEngine()
        assert engine.supports(temp_dir / "image.PNG") is True
        assert engine.supports(temp_dir / "image.JPG") is True


class TestPillowEngineConvert:
    """Test the convert method of PillowEngine."""

    def test_convert_png_to_jpg(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "output.jpg"
        
        result = engine.convert(sample_image, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        # Verify the output is actually a JPEG
        with Image.open(output_path) as img:
            assert img.format == 'JPEG'

    def test_convert_png_to_webp(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "output.webp"
        
        result = engine.convert(sample_image, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.format == 'WEBP'

    def test_convert_png_to_png(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "output.png"
        
        result = engine.convert(sample_image, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.format == 'PNG'

    def test_convert_with_explicit_format(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "output"  # No extension
        
        result = engine.convert(sample_image, output_path, target_format='jpg')
        
        assert result == output_path
        assert output_path.exists()

    def test_convert_rgba_to_jpg(self, sample_rgba_image, temp_dir):
        """Test that RGBA images are properly converted to JPG with white background."""
        engine = PillowEngine()
        output_path = temp_dir / "output.jpg"
        
        result = engine.convert(sample_rgba_image, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.format == 'JPEG'
            assert img.mode == 'RGB'

    def test_convert_unsupported_format_raises(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "output.gif"
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            engine.convert(sample_image, output_path, target_format='gif')


class TestPillowEngineResize:
    """Test the resize functionality of PillowEngine."""

    def test_resize_maintain_aspect_ratio(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "resized.png"
        
        result = engine.resize(sample_image, output_path, size=(50, 50))
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            # With maintain_aspect_ratio=True, thumbnail ensures max dimension is 50
            assert img.width <= 50
            assert img.height <= 50

    def test_resize_no_aspect_ratio(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "resized.png"
        
        result = engine.resize(
            sample_image, 
            output_path, 
            size=(50, 30),
            maintain_aspect_ratio=False
        )
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.width == 50
            assert img.height == 30

    def test_convert_with_resize(self, sample_image, temp_dir):
        engine = PillowEngine()
        output_path = temp_dir / "converted_resized.jpg"
        
        result = engine.convert(
            sample_image, 
            output_path, 
            target_format='jpg',
            resize=(50, 50)
        )
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.format == 'JPEG'
            assert img.width <= 50
            assert img.height <= 50


class TestPillowEngineQuality:
    """Test quality settings for PillowEngine."""

    def test_quality_setting(self, sample_image, temp_dir):
        engine_low = PillowEngine(quality=10)
        engine_high = PillowEngine(quality=95)
        
        output_low = temp_dir / "low_quality.jpg"
        output_high = temp_dir / "high_quality.jpg"
        
        engine_low.convert(sample_image, output_low)
        engine_high.convert(sample_image, output_high)
        
        # High quality file should be larger
        assert output_high.stat().st_size > output_low.stat().st_size


class TestPillowEngineInit:
    """Test PillowEngine initialization."""

    def test_default_quality(self):
        engine = PillowEngine()
        assert engine.quality == 95

    def test_custom_quality(self):
        engine = PillowEngine(quality=80)
        assert engine.quality == 80
