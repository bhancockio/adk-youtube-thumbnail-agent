"""
Thumbnail Analyzer Agent

This module defines the thumbnail analyzer agent that processes YouTube thumbnails to 
identify their visual style characteristics and generates a comprehensive style guide.
"""

from google.adk.agents import LoopAgent, SequentialAgent

from .style_guide_generator import style_guide_generator
from .thumbnail_analysis_sequence import thumbnail_analysis_sequence

# Create the Loop Agent that will repeatedly call the analysis sequence
# until all thumbnails are processed
thumbnail_analysis_loop = LoopAgent(
    name="ThumbnailAnalysisLoop",
    max_iterations=20,  # Maximum number of iterations (should be more than max thumbnails)
    sub_agents=[
        thumbnail_analysis_sequence,  # The sequential agent that selects and analyzes thumbnails
    ],
    description="""
        Iteratively analyzes thumbnails one by one
        until all are processed
    """,
)

# Create the Sequential Agent that first loops through all thumbnails,
# then generates a comprehensive style guide
thumbnail_analyzer_agent = SequentialAgent(
    name="ThumbnailAnalyzerAgent",
    sub_agents=[
        thumbnail_analysis_loop,  # Step 1: Analyze all thumbnails in a loop
        style_guide_generator,  # Step 2: Generate style guide from all analyses
    ],
    description="""
        Analyzes multiple thumbnails from a YouTube channel,
        then creates a comprehensive style guide based on all analyses
    """,
)
