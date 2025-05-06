import os
import uuid
from typing import List, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from youtube_thumbnail_agent.shared_lib.image_utils import ensure_image_directory_exists


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Callback that executes before the model is called.
    Detects inline images in user messages and saves them to a local folder.

    Args:
        callback_context: The callback context
        llm_request: The LLM request

    Returns:
        Optional[LlmRequest]: Modified request or None if no changes
    """
    # Get the last user message
    last_user_message_parts: List[types.Part] = []
    if llm_request.contents and llm_request.contents[-1].role == "user":
        if llm_request.contents[-1].parts:
            last_user_message_parts = llm_request.contents[-1].parts

    # Debug logging for message structure
    print(f"[Image Callback] User message parts count: {len(last_user_message_parts)}")

    # Check for inline data (images)
    image_count = 0
    current_images = []

    # Ensure the images directory exists
    images_dir = ensure_image_directory_exists()

    if last_user_message_parts:
        for i, part in enumerate(last_user_message_parts):
            print(f"[Image Callback] Examining part {i}, type: {type(part)}")

            if hasattr(part, "inline_data"):
                print(f"[Image Callback] Part {i} has inline_data")
                if part.inline_data is None:
                    print("[Image Callback] inline_data is None")
                    continue

                print(f"[Image Callback] inline_data type: {type(part.inline_data)}")

                # Check mime_type
                mime_type = None
                if hasattr(part.inline_data, "mime_type"):
                    mime_type = part.inline_data.mime_type
                    print(f"[Image Callback] mime_type: {mime_type}")
                else:
                    print("[Image Callback] No mime_type attribute found")

                # Check data
                image_data = None
                if hasattr(part.inline_data, "data"):
                    image_data = part.inline_data.data
                    data_len = len(image_data) if image_data else 0
                    print(f"[Image Callback] data length: {data_len} bytes")
                else:
                    print("[Image Callback] No data attribute found")

                # Process image if it has a valid mime type and data
                if mime_type and mime_type.startswith("image/") and image_data:
                    image_count += 1
                    print(f"[Image Callback] Found image #{image_count} in part {i}")

                    # Get the extension from mime type
                    extension = mime_type.split("/")[-1]
                    if extension == "jpeg":
                        extension = "jpg"

                    # Simple naming strategy
                    image_name = f"user_image_{image_count}.{extension}"
                    image_path = os.path.join(images_dir, image_name)

                    # Save the image to the local directory
                    try:
                        print(f"[Image Callback] Saving image to: {image_path}")

                        # Write the binary data to a file
                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        # Add to current images list
                        current_images.append(image_name)
                        print(f"[Image Callback] Saved image: {image_name}")

                    except Exception as e:
                        print(f"[Image Callback] Error saving image: {str(e)}")
                        import traceback

                        traceback.print_exc()

    if image_count > 0:
        print(f"[Image Callback] Processed and saved {image_count} image(s)")
        # Update current images - replacing previous ones
        callback_context.state["current_image_filenames"] = current_images
        print(f"[Image Callback] Current images: {current_images}")
    else:
        print("[Image Callback] No images found in user message")

    # Return None to continue with the original request
    return None
