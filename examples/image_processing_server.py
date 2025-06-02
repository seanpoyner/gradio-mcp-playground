"""Image Processing Gradio MCP Server Example

This example shows how to create image processing tools as MCP servers.
"""

import gradio as gr
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np
from typing import Tuple, Optional


def resize_image(image: Image.Image, width: int, height: int, maintain_aspect: bool = True) -> Image.Image:
    """Resize an image to specified dimensions.
    
    Args:
        image: Input image
        width: Target width
        height: Target height
        maintain_aspect: Whether to maintain aspect ratio
        
    Returns:
        Resized image
    """
    if maintain_aspect:
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize((width, height), Image.Resampling.LANCZOS)


def apply_filters(image: Image.Image, filter_type: str) -> Image.Image:
    """Apply various filters to an image.
    
    Args:
        image: Input image
        filter_type: Type of filter to apply
        
    Returns:
        Filtered image
    """
    if filter_type == "Blur":
        return image.filter(ImageFilter.BLUR)
    elif filter_type == "Sharpen":
        return image.filter(ImageFilter.SHARPEN)
    elif filter_type == "Edge Enhance":
        return image.filter(ImageFilter.EDGE_ENHANCE)
    elif filter_type == "Emboss":
        return image.filter(ImageFilter.EMBOSS)
    elif filter_type == "Contour":
        return image.filter(ImageFilter.CONTOUR)
    elif filter_type == "Grayscale":
        return ImageOps.grayscale(image)
    elif filter_type == "Invert":
        return ImageOps.invert(image.convert('RGB'))
    else:
        return image


def adjust_image(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0
) -> Image.Image:
    """Adjust image properties like brightness, contrast, and saturation.
    
    Args:
        image: Input image
        brightness: Brightness factor (1.0 = original)
        contrast: Contrast factor (1.0 = original)
        saturation: Saturation factor (1.0 = original)
        
    Returns:
        Adjusted image
    """
    # Apply brightness
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)
    
    # Apply contrast
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
    
    # Apply saturation
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation)
    
    return image


def rotate_flip_image(
    image: Image.Image,
    rotation: int = 0,
    flip_horizontal: bool = False,
    flip_vertical: bool = False
) -> Image.Image:
    """Rotate and flip an image.
    
    Args:
        image: Input image
        rotation: Rotation angle (0, 90, 180, 270)
        flip_horizontal: Whether to flip horizontally
        flip_vertical: Whether to flip vertically
        
    Returns:
        Transformed image
    """
    # Apply rotation
    if rotation == 90:
        image = image.rotate(-90, expand=True)
    elif rotation == 180:
        image = image.rotate(180)
    elif rotation == 270:
        image = image.rotate(90, expand=True)
    
    # Apply flips
    if flip_horizontal:
        image = ImageOps.mirror(image)
    if flip_vertical:
        image = ImageOps.flip(image)
    
    return image


def get_image_info(image: Image.Image) -> str:
    """Get detailed information about an image.
    
    Args:
        image: Input image
        
    Returns:
        Image information as formatted text
    """
    info = f"""Image Information:
- Format: {image.format if image.format else 'Unknown'}
- Mode: {image.mode}
- Size: {image.size[0]} x {image.size[1]} pixels
- Total Pixels: {image.size[0] * image.size[1]:,}
"""
    
    # Add color information for RGB images
    if image.mode in ['RGB', 'RGBA']:
        np_image = np.array(image)
        if image.mode == 'RGBA':
            np_image = np_image[:, :, :3]  # Ignore alpha channel for stats
        
        info += f"""
Color Statistics:
- Mean RGB: ({np_image[:,:,0].mean():.1f}, {np_image[:,:,1].mean():.1f}, {np_image[:,:,2].mean():.1f})
- Std RGB: ({np_image[:,:,0].std():.1f}, {np_image[:,:,1].std():.1f}, {np_image[:,:,2].std():.1f})
"""
    
    return info


# Create interfaces
resize_interface = gr.Interface(
    fn=resize_image,
    inputs=[
        gr.Image(type="pil", label="Input Image"),
        gr.Number(label="Width", value=800, precision=0),
        gr.Number(label="Height", value=600, precision=0),
        gr.Checkbox(label="Maintain Aspect Ratio", value=True)
    ],
    outputs=gr.Image(type="pil", label="Resized Image"),
    title="Image Resizer",
    description="Resize images to specific dimensions"
)

filter_interface = gr.Interface(
    fn=apply_filters,
    inputs=[
        gr.Image(type="pil", label="Input Image"),
        gr.Dropdown(
            ["None", "Blur", "Sharpen", "Edge Enhance", "Emboss", "Contour", "Grayscale", "Invert"],
            label="Filter Type",
            value="None"
        )
    ],
    outputs=gr.Image(type="pil", label="Filtered Image"),
    title="Image Filters",
    description="Apply various filters to images"
)

adjust_interface = gr.Interface(
    fn=adjust_image,
    inputs=[
        gr.Image(type="pil", label="Input Image"),
        gr.Slider(0.1, 2.0, value=1.0, step=0.1, label="Brightness"),
        gr.Slider(0.1, 2.0, value=1.0, step=0.1, label="Contrast"),
        gr.Slider(0.0, 2.0, value=1.0, step=0.1, label="Saturation")
    ],
    outputs=gr.Image(type="pil", label="Adjusted Image"),
    title="Image Adjustments",
    description="Adjust brightness, contrast, and saturation"
)

transform_interface = gr.Interface(
    fn=rotate_flip_image,
    inputs=[
        gr.Image(type="pil", label="Input Image"),
        gr.Dropdown([0, 90, 180, 270], label="Rotation (degrees)", value=0),
        gr.Checkbox(label="Flip Horizontal"),
        gr.Checkbox(label="Flip Vertical")
    ],
    outputs=gr.Image(type="pil", label="Transformed Image"),
    title="Image Transform",
    description="Rotate and flip images"
)

info_interface = gr.Interface(
    fn=get_image_info,
    inputs=gr.Image(type="pil", label="Input Image"),
    outputs=gr.Textbox(label="Image Information", lines=10),
    title="Image Info",
    description="Get detailed information about an image"
)

# Combine all interfaces
demo = gr.TabbedInterface(
    [resize_interface, filter_interface, adjust_interface, transform_interface, info_interface],
    ["Resize", "Filters", "Adjust", "Transform", "Info"],
    title="Image Processing MCP Server"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(
        server_port=7862,
        mcp_server=True,
        server_name="0.0.0.0"
    )
