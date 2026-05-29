SENTIMENT_PROMPT = """Analyze the sentiment of these news headlines about {company}.
Classify as: positive | negative | neutral | mixed.
Also identify the top 3 most significant events mentioned.

Headlines:
{headlines}

Respond with JSON:
{{"sentiment": "...", "key_events": ["...", "...", "..."]}}"""
