SENTIMENT_PROMPT = """Analyze the sentiment of these news headlines about {company}.
Classify as: positive | negative | neutral | mixed.
Also identify the top 3 most significant events mentioned.

Headlines:
{headlines}

Respond with JSON:
{{"sentiment": "...", "key_events": ["...", "...", "..."]}}"""

REPORT_PROMPT = """You are a financial analyst. Generate a comprehensive company report based on the following data:

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
