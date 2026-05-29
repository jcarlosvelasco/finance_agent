import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Finance Agent", page_icon="📈")
st.title("Finance Agent")

ticker = st.text_input(
    "Enter a stock ticker:",
    placeholder="e.g., AAPL, NVDA, MSFT",
    value=st.session_state.get("ticker", ""),
).upper()

if st.button("Generate report", type="primary"):
    if not ticker.strip():
        st.warning("Please enter a ticker.")
    else:
        st.session_state["ticker"] = ticker
        with st.spinner("Analyzing... This may take a minute."):
            try:
                resp = httpx.get(
                    f"{API_BASE_URL}/generate_report",
                    params={"ticker": ticker},
                    timeout=180,
                )
                resp.raise_for_status()
                data = resp.json()

                if data["success"]:
                    st.markdown(data["report"])
                else:
                    st.error(f"Error: {data.get('error', 'Unknown error')}")

            except httpx.RequestError as e:
                st.error(f"Connection error: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

st.divider()
st.caption(
    "Powered by Ollama · LangGraph · yfinance · Tavily. Reports are cached for 24h."
)
