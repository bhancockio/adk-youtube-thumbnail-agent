from typing import Dict

from google.adk.tools.tool_context import ToolContext


def exit_analysis(
    tool_context: ToolContext,
) -> Dict:
    """
    Exit the thumbnail analysis loop only if all thumbnails have been analyzed.

    This function checks if all thumbnails in the thumbnail_analysis state have
    non-empty analysis strings.

    Args:
        tool_context: ADK tool context

    Returns:
        Dictionary with exit status
    """
    try:
        if tool_context:
            # Check if thumbnail_analysis exists in state
            if "thumbnail_analysis" not in tool_context.state:
                return {
                    "status": "error",
                    "message": "No thumbnail_analysis found in state. Cannot exit yet.",
                }

            analyzed_thumbnails = tool_context.state["thumbnail_analysis"]

            if not analyzed_thumbnails:
                return {
                    "status": "error",
                    "message": "thumbnail_analysis exists but is empty. Cannot exit yet.",
                }

            # Find thumbnails that haven't been analyzed yet (have empty analysis strings)
            missing_thumbnails = [
                filename
                for filename, analysis in analyzed_thumbnails.items()
                if not analysis  # Empty string evaluates to False
            ]

            if missing_thumbnails:
                return {
                    "status": "error",
                    "message": f"Cannot exit yet. {len(missing_thumbnails)} thumbnails still need analysis: {', '.join(missing_thumbnails[:3])}{' and more' if len(missing_thumbnails) > 3 else ''}",
                }

            # All thumbnails have been analyzed, set exit flag
            tool_context.state["exit_thumbnail_analysis"] = True

            # Create a summary of the analyses for easy access
            tool_context.state["thumbnail_analysis_summary"] = {
                "total_thumbnails_analyzed": len(analyzed_thumbnails),
                "thumbnails": list(analyzed_thumbnails.keys()),
            }

            return {
                "status": "success",
                "message": f"Analysis complete for all {len(analyzed_thumbnails)} thumbnails. Exiting analysis loop.",
            }

        return {
            "status": "error",
            "message": "Tool context is missing. Cannot exit analysis.",
        }

    except Exception as e:
        error_message = f"Error exiting analysis loop: {str(e)}"
        print(error_message)
        return {"status": "error", "message": error_message}
