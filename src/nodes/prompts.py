SENTIMENT_PROMPT = """Analyze the sentiment of these news headlines about {company}.

Headlines:
{headlines}

Respond ONLY with this exact JSON, no other text:
{{"sentiment": "positive|negative|neutral|mixed", "key_events": ["event1", "event2", "event3"]}}"""

REPORT_PROMPT = """You are a financial analyst. Generate a comprehensive company report based on the following data.

Report Date: {current_date}

COMPANY INFORMATION:
- Name: {name}
- Ticker: {ticker}
- Current Price: ${price:.2f}
- Market Cap: ${market_cap:.2e}
- Sector: {sector}
- Industry: {industry}

VALUATION METRICS:
- P/E Ratio: {pe_ratio:.2f}
- EPS: ${eps:.2f}
- 52-Week High: ${fifty_two_week_high:.2f}
- 52-Week Low: ${fifty_two_week_low:.2f}
- Dividend Yield: {dividend_yield:.2f}%

FINANCIAL METRICS:
- Revenue Growth: {revenue_growth:.2f}%
- Gross Margins: {gross_margins:.2f}%
- Profit Margins: {profit_margins:.2f}%
- Return on Equity: {return_on_equity:.2f}%
- Debt to Equity: {debt_to_equity:.2f}
- Free Cashflow: ${free_cashflow:.2e}
- Total Cash: ${total_cash:.2e}
- Total Debt: ${total_debt:.2e}

SENTIMENT ANALYSIS:
- Market Sentiment: {sentiment}
- Key Events: {key_events}

Based on this data, provide a professional financial report that includes:
1. Executive Summary (2-3 sentences)
2. Company Overview
3. Financial Health Assessment
4. Valuation Analysis
5. Market Sentiment and Recent Developments
6. Investment Perspective (potential risks and opportunities)
7. Key Takeaways

Provide actionable insights and clear analysis."""

JUDGE_PROMPT = """You are an expert financial analyst evaluating the quality of a company report.

ORIGINAL DATA PROVIDED:
- Company: {name} ({ticker})
- Price: ${price}, Market Cap: ${market_cap:.2e}
- Sentiment: {sentiment}
- Key Events: {key_events}

GENERATED REPORT:
{report}

Evaluate this report on the following criteria (score 1-5 each):

1. **factual_consistency**: Does the report accurately reflect the provided financial data?
2. **completeness**: Does it cover all 7 required sections (Executive Summary, Overview, Financial Health, Valuation, Sentiment, Investment Perspective, Key Takeaways)?
3. **analytical_depth**: Does it provide genuine insight beyond restating numbers?
4. **actionability**: Are the investment insights clear and actionable?
5. **coherence**: Is the report well-structured and logically consistent?

Respond ONLY with a JSON object like:
{{
  "scores": {{
    "factual_consistency": <1-5>,
    "completeness": <1-5>,
    "analytical_depth": <1-5>,
    "actionability": <1-5>,
    "coherence": <1-5>
  }},
  "overall_score": <1-5>,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "reasoning": "Brief overall justification"
}}"""
