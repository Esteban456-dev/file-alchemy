"""
PillowEngine - Image conversion and resizing engine.

Supports conversion between PNG, JPG, WEBP formats and image resizing.
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image


class PillowEngine:
    """Engine for image processing using Pillow."""

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    OUTPUT_FORMATS = {'png', 'jpg', 'webp'}

    def __init__(self, quality: int = 95):
        """
        Initialize the PillowEngine.

        Args:
            quality: JPEG/WEBP quality (1-100). Default is 95.
        """
        self.quality = quality

    def supports(self, file_path: Path) -> bool:
        """
        Check if this engine can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file is a supported image format.
        """
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        target_format: Optional[str] = None,
        resize: Optional[Tuple[int, int]] = None,
        maintain_aspect_ratio: bool = True
    ) -> Path:
        """
        Convert an image to a different format and/or resize it.

        Args:
            input_path: Path to the input image.
            output_path: Path for the output image.
            target_format: Target format ('png', 'jpg', 'webp'). 
                          If None, inferred from output_path extension.
            resize: Tuple of (width, height) for resizing.
            maintain_aspect_ratio: If True, maintains aspect ratio when resizing.

        Returns:
            Path to the converted image.

        Raises:
            ValueError: If the format is not supported.
        """
        # Open the image
        with Image.open(input_path) as img:
            # Convert to RGB if saving as JPEG and image has alpha channel
            if target_format == 'jpg' or (target_format is None and output_path.suffix.lower() in ['.jpg', '.jpeg']):
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

            # Resize if requested
            if resize:
                if maintain_aspect_ratio:
                    img.thumbnail(resize, Image.Resampling.LANCZOS)
                else:
                    img = img.resize(resize, Image.Resampling.LANCZOS)

            # Determine output format
            if target_format is None:
                suffix = output_path.suffix.lower().lstrip('.')
                if suffix == 'jpeg':
                    target_format = 'jpg'
                else:
                    target_format = suffix

            # Validate format
            if target_format not in self.OUTPUT_FORMATS:
                raise ValueError(f"Unsupported output format: {target_format}")

            # Handle JPEG format name
            save_format = 'JPEG' if target_format == 'jpg' else target_format.upper()

            # Save the image
            save_kwargs = {}
            if target_format in ('jpg', 'webp'):
                save_kwargs['quality'] = self.quality
            elif target_format == 'png':
                save_kwargs['optimize'] = True

            img.save(output_path, format=save_format, **save_kwargs)

        return output_path

    def resize(
        self,
        input_path: Path,
        output_path: Path,
        size: Tuple[int, int],
        maintain_aspect_ratio: bool = True
    ) -> Path:
        """
        Resize an image.

        Args:
            input_path: Path to the input image.
            output_path: Path for the output image.
            size: Tuple of (width, height).
            maintain_aspect_ratio: If True, maintains aspect ratio.

        Returns:
            Path to the resized image.
        """
        return self.convert(
            input_path=input_path,
            output_path=output_path,
            resize=size,
            maintain_aspect_ratio=maintain_aspect_ratio
        )
