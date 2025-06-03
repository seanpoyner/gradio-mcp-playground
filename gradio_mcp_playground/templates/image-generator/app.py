"""{{name}} - Image Generator MCP Server

AI image generation MCP server using Stable Diffusion.
"""

import gradio as gr
from PIL import Image
import numpy as np


def generate_image(
    prompt: str, negative_prompt: str = "", steps: int = 20, seed: int = -1
) -> Image.Image:
    """Generate an image from a text prompt.

    Args:
        prompt: Text description of the image to generate
        negative_prompt: What to avoid in the image
        steps: Number of inference steps
        seed: Random seed for reproduction (-1 for random)

    Returns:
        Generated image
    """
    # Placeholder implementation
    # In a real implementation, you would use a model like Stable Diffusion
    # For demo purposes, we'll create a placeholder image

    # Create a placeholder image with text
    img = Image.new("RGB", (512, 512), color="white")

    # You would replace this with actual model inference:
    # from diffusers import StableDiffusionPipeline
    # pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
    # image = pipe(prompt, negative_prompt=negative_prompt, num_inference_steps=steps).images[0]

    # For now, return placeholder
    from PIL import ImageDraw, ImageFont

    draw = ImageDraw.Draw(img)

    # Add text to show it's a placeholder
    text = f"Generated: {prompt[:30]}..."
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = None

    draw.text((10, 250), text, fill="black", font=font)
    draw.text((10, 280), f"Steps: {steps}, Seed: {seed}", fill="gray", font=font)

    return img


def generate_variations(image: Image.Image, strength: float = 0.75) -> Image.Image:
    """Generate variations of an existing image.

    Args:
        image: Input image to create variations from
        strength: How much to vary (0.0 = identical, 1.0 = completely different)

    Returns:
        Generated variation
    """
    # Placeholder - would use img2img in real implementation
    if image is None:
        return None

    # Simple filter as placeholder
    img_array = np.array(image)
    noise = np.random.normal(0, strength * 50, img_array.shape)
    varied = np.clip(img_array + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(varied)


# Create interfaces
text2img_interface = gr.Interface(
    fn=generate_image,
    inputs=[
        gr.Textbox(label="Prompt", placeholder="A beautiful sunset over mountains..."),
        gr.Textbox(label="Negative Prompt", placeholder="blurry, low quality...", value=""),
        gr.Slider(minimum=1, maximum=50, value=20, step=1, label="Steps"),
        gr.Number(label="Seed", value=-1, precision=0),
    ],
    outputs=gr.Image(label="Generated Image", type="pil"),
    title="Text to Image",
    description="Generate images from text descriptions",
    examples=[
        ["A serene lake surrounded by mountains at sunset", "blurry, low quality", 20, -1],
        ["A futuristic city with flying cars", "dark, dystopian", 30, 42],
        ["A cute robot playing with a kitten", "scary, violent", 25, -1],
    ],
)

img2img_interface = gr.Interface(
    fn=generate_variations,
    inputs=[
        gr.Image(label="Input Image", type="pil"),
        gr.Slider(minimum=0.0, maximum=1.0, value=0.75, label="Variation Strength"),
    ],
    outputs=gr.Image(label="Generated Variation", type="pil"),
    title="Image Variations",
    description="Create variations of existing images",
)

# Combine interfaces
demo = gr.TabbedInterface(
    [text2img_interface, img2img_interface], ["Text to Image", "Image Variations"], title="{{name}}"
)

# Launch as MCP server
if __name__ == "__main__":
    demo.launch(server_port={{port}}, mcp_server=True)
