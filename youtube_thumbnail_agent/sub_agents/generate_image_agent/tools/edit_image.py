"""
Tool for editing images using OpenAI's image editing API.
"""

import base64
import os
import sys
from typing import Dict, List, Optional

import google.genai.types as types
from google.adk.tools.tool_context import ToolContext
from openai import OpenAI


def edit_image(
    prompt: str,
    image_paths: List[str],
    filename: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> Dict:
    """
    Edit images using OpenAI's image editing API with gpt-image-1 model
    and save the result as an artifact.

    Args:
        prompt (str): The prompt describing how to edit/combine the images
        image_paths (List[str]): List of paths to images to edit/combine
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

        # Validate image paths
        image_files = []
        for path in image_paths:
            if not os.path.exists(path):
                return {"status": "error", "message": f"Image not found: {path}"}
            try:
                # Open images for editing
                image_files.append(open(path, "rb"))
            except Exception as e:
                # Close any opened files
                for f in image_files:
                    f.close()
                return {
                    "status": "error",
                    "message": f"Error opening image {path}: {str(e)}",
                }

        # Clean up prompt if needed
        clean_prompt = prompt.strip()

        # Add YouTube thumbnail context if not mentioned
        if "youtube thumbnail" not in clean_prompt.lower():
            clean_prompt = f"YouTube thumbnail: {clean_prompt}"

        try:
            # Edit the images using the gpt-image-1 model
            response = client.images.edit(
                model="gpt-image-1",
                image=image_files,
                prompt=clean_prompt,
            )

            # Close all image files
            for img in image_files:
                img.close()

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

                filename = f"edited_thumbnail_{int(time.time())}.png"

            # Make sure filename has .png extension
            if not filename.lower().endswith(".png"):
                filename += ".png"

            # Save as an artifact if tool_context is provided
            artifact_version = None
            if tool_context:
                # Create a Part object for the artifact
                edited_image_artifact = types.Part(
                    inline_data=types.Blob(data=image_bytes, mime_type="image/png")
                )

                try:
                    # Save the artifact
                    artifact_version = tool_context.save_artifact(
                        filename=filename, artifact=edited_image_artifact
                    )

                    # Store image artifact details in state
                    tool_context.state["edited_image_filename"] = filename
                    tool_context.state["edited_image_version"] = artifact_version

                except ValueError as e:
                    # Handle the case where artifact_service is not configured
                    return {
                        "status": "warning",
                        "message": f"Image edited but could not be saved as an artifact: {str(e)}. Is ArtifactService configured?",
                    }
                except Exception as e:
                    # Handle other potential artifact storage errors
                    return {
                        "status": "warning",
                        "message": f"Image edited but encountered an error saving as artifact: {str(e)}",
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
                    "message": f"Image edited successfully and saved as artifact '{filename}' (version {artifact_version}) and local file '{filepath}'",
                    "filepath": filepath,
                    "artifact_filename": filename,
                    "artifact_version": artifact_version,
                }
            else:
                return {
                    "status": "success",
                    "message": f"Image edited successfully and saved as local file '{filepath}'",
                    "filepath": filepath,
                }

        finally:
            # Make sure all image files are closed
            for img in image_files:
                try:
                    img.close()
                except:
                    pass

    except Exception as e:
        return {"status": "error", "message": f"Error editing image: {str(e)}"}


# Test the edit_image function if this script is run directly
if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Check if there are any images in the generated_thumbnails directory
    if not os.path.exists("generated_thumbnails"):
        print(
            "No 'generated_thumbnails' directory found. Please run create_image.py first to generate some images."
        )
        sys.exit(1)

    thumbnails = [f for f in os.listdir("generated_thumbnails") if f.endswith(".png")]

    if not thumbnails:
        print(
            "No thumbnails found in the 'generated_thumbnails' directory. Please run create_image.py first."
        )
        sys.exit(1)

    # Get paths to the images
    image_paths = [os.path.join("generated_thumbnails", thumbnails[0])]

    # Test prompt
    test_prompt = "Add a bright yellow 'NEW' banner in the top right corner and make the colors more vibrant."

    print("Testing edit_image function...")
    print(f"Prompt: {test_prompt}")
    print(f"Using image(s): {image_paths}")

    # Test the function
    result = edit_image(
        prompt=test_prompt,
        image_paths=image_paths,
        filename="edited_test_thumbnail.png",
    )

    # Print the result
    print("\nResult:")
    for key, value in result.items():
        print(f"{key}: {value}")

    # Additional success message
    if result["status"] == "success":
        print(f"\nImage successfully edited and saved to: {result['filepath']}")
        print("You can open this file to view the edited thumbnail.")
