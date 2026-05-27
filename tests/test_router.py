"""
Tests for the Router.
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile

from core.router import Router
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


class TestRouterInit:
    """Test Router initialization."""

    def test_default_engines_registered(self):
        router = Router()
        # Should have PillowEngine registered by default
        assert len(router._engines) >= 1
        assert any(isinstance(engine, PillowEngine) for engine in router._engines)


class TestRouterRegisterEngine:
    """Test registering engines with the Router."""

    def test_register_engine(self):
        router = Router()
        initial_count = len(router._engines)
        
        new_engine = PillowEngine(quality=50)
        router.register_engine(new_engine)
        
        assert len(router._engines) == initial_count + 1
        assert new_engine in router._engines


class TestRouterGetEngine:
    """Test getting engines from the Router."""

    def test_get_engine_for_png(self, temp_dir):
        router = Router()
        engine = router.get_engine(temp_dir / "image.png")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)

    def test_get_engine_for_jpg(self, temp_dir):
        router = Router()
        engine = router.get_engine(temp_dir / "image.jpg")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)

    def test_get_engine_for_webp(self, temp_dir):
        router = Router()
        engine = router.get_engine(temp_dir / "image.webp")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)

    def test_get_engine_returns_none_for_unsupported(self, temp_dir):
        router = Router()
        engine = router.get_engine(temp_dir / "document.pdf")
        
        assert engine is None

    def test_get_engine_case_insensitive(self, temp_dir):
        router = Router()
        engine = router.get_engine(temp_dir / "image.PNG")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)


class TestRouterRoute:
    """Test routing files with the Router."""

    def test_route_png(self, temp_dir):
        router = Router()
        engine = router.route(temp_dir / "image.png")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)

    def test_route_jpg(self, temp_dir):
        router = Router()
        engine = router.route(temp_dir / "image.jpeg")
        
        assert engine is not None
        assert isinstance(engine, PillowEngine)

    def test_route_unsupported_returns_none(self, temp_dir):
        router = Router()
        engine = router.route(temp_dir / "video.mp4")
        
        assert engine is None


class TestRouterSupports:
    """Test the supports method of Router."""

    def test_supports_png(self, temp_dir):
        router = Router()
        assert router.supports(temp_dir / "image.png") is True

    def test_supports_jpg(self, temp_dir):
        router = Router()
        assert router.supports(temp_dir / "image.jpg") is True

    def test_supports_webp(self, temp_dir):
        router = Router()
        assert router.supports(temp_dir / "image.webp") is True

    def test_does_not_support_pdf(self, temp_dir):
        router = Router()
        assert router.supports(temp_dir / "document.pdf") is False

    def test_does_not_support_mp4(self, temp_dir):
        router = Router()
        assert router.supports(temp_dir / "video.mp4") is False


class TestRouterIntegration:
    """Integration tests for Router with PillowEngine."""

    def test_route_and_convert(self, sample_image, temp_dir):
        router = Router()
        output_path = temp_dir / "output.jpg"
        
        engine = router.route(sample_image)
        assert engine is not None
        
        result = engine.convert(sample_image, output_path)
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.format == 'JPEG'

    def test_route_and_resize(self, sample_image, temp_dir):
        router = Router()
        output_path = temp_dir / "resized.png"
        
        engine = router.route(sample_image)
        assert engine is not None
        
        result = engine.resize(sample_image, output_path, size=(50, 50))
        
        assert result == output_path
        assert output_path.exists()
        
        with Image.open(output_path) as img:
            assert img.width <= 50
            assert img.height <= 50
