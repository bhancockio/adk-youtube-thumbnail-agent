"""Thumbnail Analysis Sequence

This module defines a sequential agent that first selects a thumbnail to analyze, 
then analyzes it in detail.
"""

from google.adk.agents import SequentialAgent

from .thumbnail_analyzer import thumbnail_analyzer
from .thumbnail_selector import thumbnail_selector

# Create a Sequential Agent that first selects a thumbnail,
# then analyzes the selected thumbnail
thumbnail_analysis_sequence = SequentialAgent(
    name="ThumbnailAnalysisSequence",
    sub_agents=[
        thumbnail_selector,  # Step 1: Select which thumbnail to analyze
        thumbnail_analyzer,  # Step 2: Analyze the selected thumbnail
    ],
    description="""
        Processes thumbnails one at a time by:
        1. Selecting the next thumbnail that needs analysis
        2. Performing detailed visual analysis of the selected thumbnail
    """,
)
