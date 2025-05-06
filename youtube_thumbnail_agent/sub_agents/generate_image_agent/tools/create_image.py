"""
Tool for creating images using OpenAI's image generation API.
"""

import base64
import os
from typing import Dict, Optional

import google.genai.types as types
from google.adk.tools.tool_context import ToolContext
from openai import OpenAI

from ....constants import THUMBNAIL_IMAGE_SIZE


def create_image(
    prompt: str,
    filename: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> Dict:
    """
    Create an image using OpenAI's image generation API with gpt-image-1 model
    and save it as an artifact.

    Args:
        prompt (str): The prompt to generate an image from
        filename (str, optional): Filename to save the image as
        tool_context (ToolContext, optional): The tool context

    Returns:
        dict: Result containing status and message
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "message": "OPENAI_API_KEY not found in environment variables",
            }

        client = OpenAI(api_key=api_key)

        # Clean up prompt if needed
        clean_prompt = prompt.strip()

        # Add YouTube thumbnail context if not mentioned
        if "youtube thumbnail" not in clean_prompt.lower():
            clean_prompt = f"YouTube thumbnail: {clean_prompt}"

        # Generate the image
        response = client.images.generate(
            model="gpt-image-1",
            prompt=clean_prompt,
            n=1,
            size=THUMBNAIL_IMAGE_SIZE,  # Using the constant for YouTube thumbnail size
        )

        # Get the base64 image data
        if response and response.data and len(response.data) > 0:
            image_base64 = response.data[0].b64_json
            if image_base64:
                image_bytes = base64.b64decode(image_base64)
            else:
                return {
                    "status": "error",
                    "message": "No image data returned from the API",
                }
        else:
            return {
                "status": "error",
                "message": "No data returned from the API",
            }

        # Generate filename if not provided
        if not filename:
            import time

            filename = f"thumbnail_{int(time.time())}.png"

        # Make sure filename has .png extension
        if not filename.lower().endswith(".png"):
            filename += ".png"

        # Save as an artifact if tool_context is provided
        artifact_version = None
        if tool_context:
            # Create a Part object for the artifact
            image_artifact = types.Part(
                inline_data=types.Blob(data=image_bytes, mime_type="image/png")
            )

            try:
                # Save the artifact
                artifact_version = tool_context.save_artifact(
                    filename=filename, artifact=image_artifact
                )

                # Store image path in state for reference
                tool_context.state["image_filename"] = filename
                tool_context.state["image_version"] = artifact_version

            except ValueError as e:
                # Handle the case where artifact_service is not configured
                return {
                    "status": "warning",
                    "message": f"Image generated but could not be saved as an artifact: {str(e)}. Is ArtifactService configured?",
                }
            except Exception as e:
                # Handle other potential artifact storage errors
                return {
                    "status": "warning",
                    "message": f"Image generated but encountered an error saving as artifact: {str(e)}",
                }

        # Create directory for local file saving (as a backup/for testing)
        os.makedirs("generated_thumbnails", exist_ok=True)

        # Save the image locally as well
        filepath = os.path.join("generated_thumbnails", filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # Return success with artifact details if available
        if artifact_version is not None:
            return {
                "status": "success",
                "message": f"Image created successfully and saved as artifact '{filename}' (version {artifact_version}) and local file '{filepath}'",
                "filepath": filepath,
                "artifact_filename": filename,
                "artifact_version": artifact_version,
            }
        else:
            return {
                "status": "success",
                "message": f"Image created successfully and saved as local file '{filepath}'",
                "filepath": filepath,
            }

    except Exception as e:
        return {"status": "error", "message": f"Error creating image: {str(e)}"}


# Test the create_image function if this script is run directly
if __name__ == "__main__":
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Test prompt
    test_prompt = "A professional YouTube thumbnail for a video about creating AI agents. Include a computer screen with glowing code, a robot assistant, and a modern tech aesthetic. Use vibrant blue and purple colors."

    print("Testing create_image function...")
    print(f"Prompt: {test_prompt}")
    print(f"Using image size: {THUMBNAIL_IMAGE_SIZE}")

    # Test the function
    result = create_image(prompt=test_prompt, filename="test_thumbnail.png")

    # Print the result
    print("\nResult:")
    for key, value in result.items():
        print(f"{key}: {value}")

    # Additional success message
    if result["status"] == "success":
        print(f"\nImage successfully created and saved to: {result['filepath']}")
        print("You can open this file to view the generated thumbnail.")
