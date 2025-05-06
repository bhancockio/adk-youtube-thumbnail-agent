import os
import os.path
import re
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext

# Load environment variables
load_dotenv()


def ensure_reference_images_dir():
    """Ensure the reference_images directory exists."""
    ref_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "reference_images",
    )
    os.makedirs(ref_dir, exist_ok=True)
    return ref_dir


def download_thumbnail(url: str, save_path: str, index: int) -> Optional[str]:
    """Download a thumbnail from URL."""
    response = requests.get(url)

    if response.status_code == 200:
        # Save the image
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path
    else:
        print(
            f"Failed to download thumbnail {index} with status code {response.status_code}"
        )
        return None


def extract_channel_id(channel_name: str) -> Optional[str]:
    """Extract channel ID from different formats of channel names."""
    # If it's already a channel ID format
    if re.match(r"^[A-Za-z0-9_-]{24}$", channel_name):
        return channel_name

    # If it's a handle or user format
    if channel_name.startswith("@"):
        return channel_name  # Return as is, we'll handle it in the API call

    # If it's a full URL
    channel_url_match = re.search(
        r"youtube\.com/(?:channel|c|user)/([^/]+)", channel_name
    )
    if channel_url_match:
        return channel_url_match.group(1)

    # If it's a handle URL
    handle_url_match = re.search(r"youtube\.com/(@[^/]+)", channel_name)
    if handle_url_match:
        return handle_url_match.group(1)

    # Return as-is if nothing matches, assuming it might be a valid input
    return channel_name


def scrape_channel(
    tool_context: ToolContext,
    channel_name: str,
) -> Dict:
    """
    Scrape thumbnails from a YouTube channel.

    Args:
        tool_context: ADK tool context
        channel_name: YouTube channel name/ID/handle

    Returns:
        Dictionary with scraping results
    """
    num_thumbnails = 5
    try:
        # Extract channel ID if needed
        channel_id = extract_channel_id(channel_name)
        if not channel_id:
            return {
                "status": "error",
                "message": f"Could not extract channel ID from: {channel_name}",
            }

        # Prepare reference images directory
        ref_dir = ensure_reference_images_dir()

        # Get YouTube API key from environment variables
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "message": "YouTube API key not found in environment variables. Please add YOUTUBE_API_KEY to your .env file.",
            }

        # Build API URL for channel lookup
        channel_url = None
        if channel_id.startswith("@"):
            # Handle format, need to get the channel ID first
            handle_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={channel_id}&type=channel&key={api_key}"
            handle_response = requests.get(handle_url)
            if handle_response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to look up channel with handle {channel_id}. Status code: {handle_response.status_code}",
                }

            handle_data = handle_response.json()
            if not handle_data.get("items"):
                return {
                    "status": "error",
                    "message": f"No channel found for handle {channel_id}",
                }

            # Get the actual channel ID
            channel_id = handle_data["items"][0]["snippet"]["channelId"]

        # Now build URL for video lookup with the channel ID
        channel_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults={num_thumbnails}&order=date&type=video&key={api_key}"

        # Fetch videos from the channel
        response = requests.get(channel_url)
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to fetch videos from the channel. Status code: {response.status_code}",
            }

        data = response.json()

        # Check if we have videos
        if not data.get("items"):
            return {
                "status": "error",
                "message": f"No videos found for channel {channel_name}",
            }

        # Extract and download thumbnails
        thumbnails: List[str] = []

        # Initialize thumbnail_analysis in state if necessary
        if tool_context and "thumbnail_analysis" not in tool_context.state:
            tool_context.state["thumbnail_analysis"] = {}

        for i, item in enumerate(data["items"]):
            if i >= num_thumbnails:
                break

            thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"]

            # Save the thumbnail
            thumbnail_filename = f"channel_thumbnail_{i+1}.jpg"
            save_path = os.path.join(ref_dir, thumbnail_filename)

            result = download_thumbnail(thumbnail_url, save_path, i + 1)
            if result:
                thumbnails.append(thumbnail_filename)

                # Add to thumbnail_analysis with empty string value for later analysis
                if tool_context:
                    tool_context.state["thumbnail_analysis"][thumbnail_filename] = ""

        if not thumbnails:
            return {
                "status": "warning",
                "message": f"Could not download any thumbnails for {channel_name}",
            }

        # Return success
        return {
            "status": "success",
            "message": f"Successfully scraped {len(thumbnails)} thumbnails from {channel_name}",
            "channel_name": channel_name,
            "thumbnails": thumbnails,
        }

    except Exception as e:
        error_message = f"Error scraping channel: {str(e)}"
        print(error_message)
        return {"status": "error", "message": error_message}
