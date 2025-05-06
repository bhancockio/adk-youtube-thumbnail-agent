import os
from typing import Dict, List

from google.adk.tools.tool_context import ToolContext


def list_thumbnails(
    tool_context: ToolContext,
) -> Dict:
    """
    List all thumbnail images in the reference_images directory.

    NOTE: This tool is primarily for debugging or edge cases. In normal operation,
    thumbnails are pre-populated in the state["thumbnail_analysis"] dictionary, and
    you should work with that instead of calling this function.

    Args:
        tool_context: ADK tool context

    Returns:
        Dictionary with list of thumbnail filenames
    """
    try:
        # Find the reference_images directory
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        ref_dir = os.path.join(base_dir, "reference_images")

        # Check if directory exists
        if not os.path.exists(ref_dir):
            return {
                "status": "error",
                "message": "Reference images directory not found",
            }

        # Get all image files in the directory
        image_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        thumbnails: List[str] = []

        for filename in os.listdir(ref_dir):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                thumbnails.append(filename)

        if not thumbnails:
            return {
                "status": "warning",
                "message": "No thumbnail images found in reference_images directory",
                "thumbnails": [],
            }

        # Compare with what's in state (for debugging purposes)
        if tool_context and "thumbnail_analysis" in tool_context.state:
            state_thumbnails = set(tool_context.state["thumbnail_analysis"].keys())
            disk_thumbnails = set(thumbnails)

            # Check for thumbnails in state but not on disk
            missing_on_disk = state_thumbnails - disk_thumbnails
            # Check for thumbnails on disk but not in state
            missing_in_state = disk_thumbnails - state_thumbnails

            if missing_on_disk or missing_in_state:
                return {
                    "status": "warning",
                    "message": f"Discrepancy found between state and disk. {len(missing_on_disk)} thumbnails in state but not on disk. {len(missing_in_state)} thumbnails on disk but not in state.",
                    "thumbnails": thumbnails,
                    "missing_on_disk": list(missing_on_disk),
                    "missing_in_state": list(missing_in_state),
                }

        # Update state with current thumbnail count
        if tool_context:
            tool_context.state["total_thumbnails"] = len(thumbnails)

        return {
            "status": "success",
            "message": f"Found {len(thumbnails)} thumbnail images",
            "thumbnails": thumbnails,
        }

    except Exception as e:
        error_message = f"Error listing thumbnails: {str(e)}"
        print(error_message)
        return {"status": "error", "message": error_message, "thumbnails": []}
