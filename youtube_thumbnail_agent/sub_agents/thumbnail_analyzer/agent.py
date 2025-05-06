"""
Thumbnail Analyzer Agent

This module defines the thumbnail analyzer agent that processes YouTube thumbnails to 
identify their visual style characteristics and generates a comprehensive style guide.
"""

from google.adk.agents import LoopAgent

from .thumbnail_loop_analyzer import thumbnail_analyzer

# Create the Loop Agent that will repeatedly call the analyzer
# until all thumbnails are processed
thumbnail_analyzer_agent = LoopAgent(
    name="ThumbnailAnalysisLoop",
    max_iterations=20,  # Maximum number of iterations (should be more than max thumbnails)
    sub_agents=[
        thumbnail_analyzer,
    ],
    description="""
        Iteratively analyzes thumbnails one by one
        until all are processed and a style guide is created
    """,
)
