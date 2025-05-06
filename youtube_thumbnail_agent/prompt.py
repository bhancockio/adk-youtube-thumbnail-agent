"""
Template prompts for YouTube thumbnail generation.
"""

# Base prompt for generating thumbnail descriptions
THUMBNAIL_DESCRIPTION_PROMPT = """
Create a detailed description for a YouTube thumbnail based on the following details:

Title: {title}
Topic: {topic}
Target Audience: {audience}
Channel Style/Branding: {branding}
Additional Elements: {elements}

The description should include:
1. Overall composition and layout
2. Main visual elements and their placement
3. Text overlay recommendations (if any)
4. Color scheme and lighting
5. Background design
6. Any specific emotions or expressions to convey

Make sure the thumbnail will be eye-catching, clearly communicate the topic, and encourage clicks.
"""

# Prompt for thumbnail style analysis
THUMBNAIL_STYLE_ANALYSIS_PROMPT = """
Analyze the following YouTube channel's thumbnail style:

Channel Name: {channel_name}
Niche/Content Type: {niche}
Current Thumbnail Description: {current_style}

Provide insights on:
1. Visual consistency and branding elements
2. Color schemes and patterns
3. Text usage and typography
4. Image composition techniques
5. Emotional triggers utilized
6. Areas for potential improvement

This analysis will help inform future thumbnail designs that maintain brand consistency while improving performance.
"""

# Prompt for A/B testing thumbnail variants
THUMBNAIL_AB_TEST_PROMPT = """
Create two different thumbnail concepts for A/B testing based on the following video details:

Video Title: {title}
Content Summary: {summary}
Target Audience: {audience}
Key Message/Hook: {hook}

For each variation:
1. Describe the visual composition in detail
2. Explain the psychological triggers employed
3. Specify text placement and wording (if any)
4. Outline the color strategy
5. Predict how it might perform with the target audience

These variations should test different approaches while maintaining alignment with the video content.
"""
