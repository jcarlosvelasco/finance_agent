import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Finance Agent", page_icon="📈")
st.title("Finance Agent")

for key in ("thread_id", "review_data", "report", "error_msg"):
    if key not in st.session_state:
        st.session_state[key] = None

ticker = st.text_input(
    "Enter a stock ticker:",
    placeholder="e.g., AAPL, NVDA, MSFT",
    value=st.session_state.get("ticker", ""),
).upper()

generate = st.button("Generate report", type="primary")

if generate:
    if not ticker.strip():
        st.warning("Please enter a ticker.")
    else:
        st.session_state["ticker"] = ticker
        for key in ("thread_id", "review_data", "report", "error_msg"):
            st.session_state[key] = None
        with st.spinner("Analyzing... This may take a minute."):
            try:
                resp = httpx.get(
                    f"{API_BASE_URL}/generate_report",
                    params={"ticker": ticker},
                    timeout=180,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") == "awaiting_review":
                    st.session_state["thread_id"] = data["thread_id"]
                    st.session_state["review_data"] = data["data"]
                elif data.get("success"):
                    st.session_state["report"] = data["report"]
                else:
                    st.session_state["error_msg"] = data.get("error", "Unknown error")
            except httpx.RequestError as e:
                st.session_state["error_msg"] = f"Connection error: {e}"
            except Exception as e:
                st.session_state["error_msg"] = f"Unexpected error: {e}"
        st.rerun()

if st.session_state["review_data"]:
    rd = st.session_state["review_data"]
    company = rd.get("company", {})

    st.subheader(f"Review data for {rd['ticker']}")
    st.info(
        "Review the collected data below. Approve to generate the report, "
        "or reject with feedback."
    )

    mcols = st.columns(4)
    mcols[0].metric("Price", f"${company.get('price', 'N/A')}")
    mcols[1].metric("Market Cap", f"${company.get('market_cap', 0):.0f}")
    mcols[2].metric("P/E Ratio", f"{company.get('pe_ratio', 'N/A')}")
    mcols[3].metric("EPS", f"${company.get('eps', 'N/A')}")

    mcols2 = st.columns(4)
    mcols2[0].metric("Sector", company.get("sector", "N/A"))
    mcols2[1].metric("Dividend Yield", f"{company.get('dividend_yield', 'N/A')}%")
    mcols2[2].metric("52W High", f"${company.get('52w_high', 'N/A')}")
    mcols2[3].metric("52W Low", f"${company.get('52w_low', 'N/A')}")

    with st.expander("More financial details", expanded=False):
        st.json(company)

    st.markdown(f"**Sentiment:** {rd.get('sentiment', 'N/A')}")
    st.markdown(f"**News count:** {rd.get('news_count', 0)}")

    if rd.get("key_events"):
        st.markdown("**Key events:**")
        for ev in rd["key_events"]:
            st.markdown(f"- {ev}")

    st.divider()

    feedback = st.text_area(
        "Feedback (only for rejection):",
        placeholder="e.g., The revenue growth seems incorrect",
    )

    acols = st.columns(2)
    with acols[0]:
        approve = st.button("Approve", type="primary", use_container_width=True)
    with acols[1]:
        reject = st.button("Reject", use_container_width=True)

    if approve:
        with st.spinner("Generating report..."):
            try:
                resp = httpx.post(
                    f"{API_BASE_URL}/review",
                    json={
                        "thread_id": st.session_state["thread_id"],
                        "approved": True,
                    },
                    timeout=300,
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("success"):
                    st.session_state["report"] = data["report"]
                else:
                    st.session_state["error_msg"] = data.get("error", "Unknown error")
                st.session_state["review_data"] = None
                st.rerun()
            except httpx.RequestError as e:
                st.session_state["error_msg"] = f"Connection error: {e}"
            except Exception as e:
                st.session_state["error_msg"] = f"Unexpected error: {e}"

    if reject:
        with st.spinner("Cancelling..."):
            try:
                resp = httpx.post(
                    f"{API_BASE_URL}/review",
                    json={
                        "thread_id": st.session_state["thread_id"],
                        "approved": False,
                        "feedback": feedback or None,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state["error_msg"] = data.get("error", "Report rejected")
                st.session_state["review_data"] = None
                st.rerun()
            except httpx.RequestError as e:
                st.session_state["error_msg"] = f"Connection error: {e}"
            except Exception as e:
                st.session_state["error_msg"] = f"Unexpected error: {e}"

if st.session_state["report"]:
    st.subheader(f"Report for {st.session_state.get('ticker', '')}")
    st.markdown(st.session_state["report"])

if st.session_state["error_msg"]:
    st.error(st.session_state["error_msg"])

st.divider()
st.caption(
    "Powered by Ollama · LangGraph · yfinance · Tavily. Reports are cached for 24h."
)
