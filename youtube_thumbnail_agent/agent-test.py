"""
Test agent for handling image uploads and saving them to artifacts.
"""

import base64
import io
import os
import uuid
from typing import Any, Dict, List, Optional

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.tool_context import ToolContext
from google.genai import types


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Callback that executes before the model is called.
    Detects inline images in user messages and saves them as artifacts.

    Args:
        callback_context: The callback context
        llm_request: The LLM request

    Returns:
        Optional[LlmRequest]: Modified request or None if no changes
    """
    print("[Callback] Before model call starting")

    # Get the last user message
    last_user_message_parts: List[types.Part] = []
    if llm_request.contents and llm_request.contents[-1].role == "user":
        if llm_request.contents[-1].parts:
            last_user_message_parts = llm_request.contents[-1].parts

    # Debug logging for message structure
    print(f"[Callback] User message parts count: {len(last_user_message_parts)}")

    # Check for inline data (images)
    image_count = 0
    if last_user_message_parts:
        for i, part in enumerate(last_user_message_parts):
            print(f"[Callback] Examining part {i}, type: {type(part)}")
            print(f"[Callback] Part {i} dir attributes: {dir(part)}")

            if hasattr(part, "inline_data"):
                print(f"[Callback] Part {i} has inline_data")
                if part.inline_data is None:
                    print("[Callback] inline_data is None")
                    continue

                print(f"[Callback] inline_data type: {type(part.inline_data)}")
                print(f"[Callback] inline_data dir: {dir(part.inline_data)}")

                # Inspect the Blob object more thoroughly
                if isinstance(part.inline_data, types.Blob):
                    print("[Callback] inline_data is a types.Blob instance")

                    # Get all attributes of the Blob instance
                    blob_attrs = {}
                    for attr in dir(part.inline_data):
                        if not attr.startswith("_"):  # Skip private attributes
                            try:
                                value = getattr(part.inline_data, attr)
                                # If it's a method, we don't want to call it
                                if not callable(value):
                                    blob_attrs[attr] = (
                                        str(value)[:100] if value is not None else None
                                    )
                            except Exception as e:
                                blob_attrs[attr] = f"Error accessing: {str(e)}"

                    print(f"[Callback] Blob attributes: {blob_attrs}")

                    # Check for mime_type field specifically
                    if hasattr(part.inline_data, "mime_type"):
                        print(
                            f"[Callback] Blob.mime_type: {part.inline_data.mime_type}"
                        )

                    # Check for data field specifically
                    if hasattr(part.inline_data, "data"):
                        data = part.inline_data.data
                        if data is not None:
                            data_type = type(data)
                            data_size = (
                                len(data) if hasattr(data, "__len__") else "unknown"
                            )
                            print(f"[Callback] Blob.data type: {data_type}")
                            print(f"[Callback] Blob.data size: {data_size} bytes")
                            # If it's bytes, show a preview
                            if isinstance(data, bytes):
                                print(f"[Callback] Blob.data preview: {data[:20]}...")
                        else:
                            print("[Callback] Blob.data is None")

                # Check mime_type
                mime_type = None
                if hasattr(part.inline_data, "mime_type"):
                    mime_type = part.inline_data.mime_type
                    print(f"[Callback] mime_type: {mime_type}")
                else:
                    print("[Callback] No mime_type attribute found")

                # Check data
                image_data = None
                if hasattr(part.inline_data, "data"):
                    image_data = part.inline_data.data
                    data_len = len(image_data) if image_data else 0
                    print(f"[Callback] data length: {data_len} bytes")
                else:
                    print("[Callback] No data attribute found")

                # Process image if it has a valid mime type and data
                if mime_type and mime_type.startswith("image/") and image_data:
                    image_count += 1
                    print(f"[Callback] Found image #{image_count} in part {i}")

                    # Generate a unique name for the image
                    extension = mime_type.split("/")[-1]
                    if extension == "jpeg":
                        extension = "jpg"

                    image_name = (
                        f"user_image_{image_count}_{uuid.uuid4().hex[:8]}.{extension}"
                    )

                    # Save the image as an artifact
                    try:
                        print(f"[Callback] Saving image as artifact: {image_name}")

                        # Log data type
                        print(f"[Callback] Image data type: {type(image_data)}")

                        image_artifact = types.Part.from_bytes(
                            data=image_data,
                            mime_type=mime_type,
                        )

                        version = callback_context.save_artifact(
                            filename=image_name,
                            artifact=image_artifact,
                        )
                        callback_context.state["latest_artifact_filename"] = image_name
                        print(
                            f"[Callback] Saved image as artifact: {image_name} (ID: {version})"
                        )

                    except Exception as e:
                        print(f"[Callback] Error saving image: {str(e)}")
                        import traceback

                        traceback.print_exc()

    if image_count > 0:
        print(f"[Callback] Processed and saved {image_count} image(s) as artifacts")
    else:
        print("[Callback] No images found in user message")

    # Return the original request (no modifications needed)
    return None


def list_images(tool_context: ToolContext) -> Dict:
    """
    List all saved image artifacts.

    Args:
        tool_context (ToolContext): The tool context

    Returns:
        dict: Status and list of images
    """
    try:
        # Get list of artifacts from the same mechanism we used in before_model_callback
        # We can use tool_context's built-in method
        artifacts = tool_context.list_artifacts()

        # If artifacts is None or empty, return an empty list
        if not artifacts:
            return {
                "status": "success",
                "message": "No images found",
                "images": [],
                "count": 0,
            }

        # Prepare list of images with proper properties
        image_artifacts = []
        for artifact_name in artifacts:
            # Filter to only include images by checking the filename
            if isinstance(artifact_name, str) and any(
                artifact_name.lower().endswith(ext)
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
            ):
                image_artifacts.append(
                    {
                        "id": artifact_name,  # Use the name as the ID
                        "name": artifact_name,
                        "created_at": "unknown",  # We don't have this info from list_artifacts
                    }
                )

        tool_context.state["latest_artifact_filename"] = image_artifacts[0]["name"]

        return {
            "status": "success",
            "images": image_artifacts,
            "count": len(image_artifacts),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to list images: {str(e)}"}


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback that executes after the agent has processed a message.
    Adds the latest image artifact to the response.

    Args:
        callback_context: The callback context

    Returns:
        Optional[types.Content]: Modified content or None if no changes
    """
    print("[Callback] After agent callback starting")

    # Get the latest artifact filename from state
    latest_artifact_filename = callback_context.state.get(
        "latest_artifact_filename", None
    )
    if not latest_artifact_filename:
        print("[Callback] No latest artifact filename found")
        return None

    try:
        # Load the artifact
        artifact = callback_context.load_artifact(latest_artifact_filename)
        if not artifact or not artifact.inline_data:
            print(f"[Callback] Could not load artifact: {latest_artifact_filename}")
            return None

        # Create parts with original text (if available)
        text_part = types.Part(text="Response from AI assistant with added image")

        # Extract data from the artifact
        mime_type = artifact.inline_data.mime_type

        print(f"[Callback] Using image with mime_type: {mime_type}")

        # Handle JPEG mime type
        if mime_type == "image/jpeg":
            mime_type = "image/jpg"

        # Create parts list with text and image
        new_parts = [
            text_part,
            types.Part(text=f"\n\nHere's the latest image: {latest_artifact_filename}"),
            types.Part(
                file_data=types.FileData(
                    file_uri=latest_artifact_filename,
                    mime_type=mime_type,
                )
            ),
        ]

        # Create new Content to replace the agent's response
        modified_content = types.Content(role="model", parts=new_parts)

        print(
            f"[Callback] Successfully added image {latest_artifact_filename} to response"
        )
        return modified_content

    except Exception as e:
        print(f"[Callback] Error in after_agent_callback: {str(e)}")
        import traceback

        traceback.print_exc()
        return None  # Return None to use the original response


root_agent = Agent(
    name="youtube_thumbnail_agent",
    model="gemini-2.5-flash-preview-04-17",
    description="Image Upload Testing Agent",
    instruction="""
    You are a helpful agent that handles images and answers questions from users.
    
    You can detect when users upload images and you will automatically save them as artifacts.
    
    Use the tools provided to you when needed to help users manage their images.
    """,
    tools=[list_images],
    before_model_callback=before_model_callback,
    after_agent_callback=after_agent_callback,
)
