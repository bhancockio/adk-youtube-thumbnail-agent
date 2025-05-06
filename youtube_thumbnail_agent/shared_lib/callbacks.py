import os
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse


def ensure_thumbnail_assets_directory_exists():
    """
    Ensure that the thumbnail_assets directory exists, creating it if necessary.

    Returns:
        str: Path to the thumbnail_assets directory
    """
    # Get the absolute path to the repository root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, "../.."))

    # Create the images directory path
    assets_dir = os.path.join(repo_root, "thumbnail_assets")

    # Create the directory if it doesn't exist
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"Created thumbnail_assets directory at {assets_dir}")

    return assets_dir


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Callback that executes before the model is called.
    Detects and saves inline images from user messages to thumbnail_assets folder
    for use by the generate_image_agent.

    Args:
        callback_context: The callback context
        llm_request: The LLM request

    Returns:
        Optional[LlmResponse]: None to allow normal processing
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    print(f"[Image Callback] Processing for agent: {agent_name} (Inv: {invocation_id})")

    # Ensure thumbnail_assets directory exists
    assets_dir = ensure_thumbnail_assets_directory_exists()

    # Get the last user message parts
    last_user_message_parts = []
    if llm_request.contents and llm_request.contents[-1].role == "user":
        if llm_request.contents[-1].parts:
            last_user_message_parts = llm_request.contents[-1].parts

    print(f"[Image Callback] User message parts count: {len(last_user_message_parts)}")

    # Process any image parts we found
    image_count = 0

    for part in last_user_message_parts:
        # Debug info
        print(f"[Image Callback] Examining part type: {type(part)}")

        # Make sure it's an image with mime type and data
        if not hasattr(part, "inline_data") or not part.inline_data:
            continue

        mime_type = getattr(part.inline_data, "mime_type", None)
        if not mime_type or not mime_type.startswith("image/"):
            continue

        image_data = getattr(part.inline_data, "data", None)
        if not image_data:
            continue

        # We have an image to save
        image_count += 1
        print(f"[Image Callback] Found image #{image_count}")

        # Get the file extension from mime type
        extension = mime_type.split("/")[-1]
        if extension == "jpeg":
            extension = "jpg"

        # Generate simple sequential filename
        image_name = f"user_asset_{image_count}.{extension}"
        image_path = os.path.join(assets_dir, image_name)

        # Save the image
        try:
            print(f"[Image Callback] Saving image to: {image_path}")
            with open(image_path, "wb") as f:
                f.write(image_data)
            print(f"[Image Callback] Saved image: {image_name}")
        except Exception as e:
            print(f"[Image Callback] Error saving image: {str(e)}")

    # Log the total number of images processed
    if image_count > 0:
        print(f"[Image Callback] Saved {image_count} images to {assets_dir}")

    # Continue with normal execution
    return None
