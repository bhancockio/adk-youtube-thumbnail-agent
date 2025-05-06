import os
import os.path
from typing import Dict, Optional

import google.genai.types as types
from google.adk.tools.tool_context import ToolContext


def analyze_thumbnail(
    tool_context: ToolContext,
    thumbnail_filename: str,
) -> Dict:
    """
    Load a thumbnail image as an artifact for the multimodal model to analyze.

    Args:
        tool_context: ADK tool context
        thumbnail_filename: The filename of the thumbnail to analyze

    Returns:
        Dictionary with the thumbnail image as an artifact
    """
    try:
        # Find the reference_images directory
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        ref_dir = os.path.join(base_dir, "reference_images")

        # Verify the thumbnail exists
        thumbnail_path = os.path.join(ref_dir, thumbnail_filename)
        if not os.path.exists(thumbnail_path):
            return {
                "status": "error",
                "message": f"Thumbnail file not found: {thumbnail_filename}",
            }

        # Verify thumbnail_analysis exists in state
        if "thumbnail_analysis" not in tool_context.state:
            # If not, create it with an empty entry for this thumbnail
            tool_context.state["thumbnail_analysis"] = {thumbnail_filename: ""}
        elif thumbnail_filename not in tool_context.state["thumbnail_analysis"]:
            # If thumbnail isn't in the dictionary, add it
            tool_context.state["thumbnail_analysis"][thumbnail_filename] = ""

        # Read the image file
        with open(thumbnail_path, "rb") as f:
            image_data = f.read()

        # Create an artifact with the image data
        image_artifact = types.Part(
            inline_data=types.Blob(mime_type="image/jpeg", data=image_data)
        )

        # Return success with the image artifact
        return {
            "status": "success",
            "message": f"Thumbnail loaded: {thumbnail_filename}",
            "thumbnail": thumbnail_filename,
            "image": image_artifact,
        }

    except Exception as e:
        error_message = f"Error loading thumbnail: {str(e)}"
        print(error_message)
        return {"status": "error", "message": error_message}
