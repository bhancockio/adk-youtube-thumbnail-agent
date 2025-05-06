import os
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from youtube_thumbnail_agent.shared_lib.image_utils import ensure_image_directory_exists


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback that executes before the agent is called.
    Detects and saves inline images from user messages.

    Args:
        callback_context: The callback context

    Returns:
        Optional[types.Content]: None to allow normal agent execution
    """
    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    print(f"[Image Callback] Processing for agent: {agent_name} (Inv: {invocation_id})")

    # Ensure images directory exists
    images_dir = ensure_image_directory_exists()

    # Check for new message content in the conversation
    try:
        # Get access to current state and message parts
        image_parts = []

        # Try to get message parts from the current context
        conversation = getattr(callback_context, "conversation", None)
        if conversation and hasattr(conversation, "messages"):
            # Find the latest user message
            for message in reversed(conversation.messages):
                if message.role == "user":
                    # Extract any image parts
                    for part in message.parts:
                        if hasattr(part, "inline_data") and part.inline_data:
                            image_parts.append(part)
                    break

        # Process any image parts we found
        current_images = []
        image_count = 0

        for part in image_parts:
            # Make sure it's an image with mime type and data
            mime_type = getattr(part.inline_data, "mime_type", None)
            if not mime_type or not mime_type.startswith("image/"):
                continue

            image_data = getattr(part.inline_data, "data", None)
            if not image_data:
                continue

            # We have an image to save
            image_count += 1

            # Get the file extension from mime type
            extension = mime_type.split("/")[-1]
            if extension == "jpeg":
                extension = "jpg"

            # Generate simple sequential filename
            image_name = f"user_image_{image_count}.{extension}"

            image_path = os.path.join(images_dir, image_name)

            # Save the image
            try:
                print(f"[Image Callback] Saving image to: {image_path}")
                with open(image_path, "wb") as f:
                    f.write(image_data)

                # Record this image
                current_images.append(image_name)
                print(f"[Image Callback] Saved image: {image_name}")
            except Exception as e:
                print(f"[Image Callback] Error saving image: {str(e)}")

        # Update state if we found any images
        if current_images:
            callback_context.state["current_image_filenames"] = current_images
            print(f"[Image Callback] Updated state with {len(current_images)} images")

    except Exception as e:
        print(f"[Image Callback] Error processing message: {str(e)}")
        import traceback

        traceback.print_exc()

    # Continue with normal agent execution
    return None
