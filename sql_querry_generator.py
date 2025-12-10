import os
import streamlit as st
import requests
import json
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(
    page_title="SQL Query Generator",
    layout="wide"
)

st.title("SQL Query Generator")
st.markdown("Convert plain English to SQL queries using AI")


if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")



with st.sidebar:
    st.header("Database Schema (Optional)")
    schema = st.text_area(
        "Paste your CREATE TABLE statements",
        height=300,
        placeholder="CREATE TABLE users (\n  user_id INT PRIMARY KEY,\n  username VARCHAR(50)\n);"
    )

description = st.text_area(
    "What data do you need?",
    height=150,
    placeholder="Examples:\n• Get all customers who made purchases over $100\n• Find the top 10 products by revenue"
)

def query_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

if st.button("Generate SQL Query", type="primary"):
    if not description:
        st.error("Please describe what data you need")
    else:
        with st.spinner("Generating query..."):
            try:
                prompt = f"""You are a SQL expert. Generate a SQL query for this request. If provided a Database schema do not use alias names for the table name.

{'DATABASE SCHEMA:\n' + schema + '\n' if schema else 'Use common table and column names.\n'}

USER REQUEST: {description}

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{"query": "SELECT statement here", "explanation": "what this query does"}}"""
                
                result = query_gemini(prompt, api_key)
                
                # Check for errors
                if "error" in result:
                    st.error(f"API Error: {result['error'].get('message', 'Unknown error')}")
                    st.code(json.dumps(result, indent=2))
                    st.stop()
                
                # Extract the text from Gemini's response
                if "candidates" in result and len(result["candidates"]) > 0:
                    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    try:
                        # Clean the response
                        generated_text = generated_text.strip()
                        
                        # Remove markdown code blocks if present
                        if "```json" in generated_text:
                            generated_text = generated_text.split("```json")[1].split("```")[0]
                        elif "```" in generated_text:
                            generated_text = generated_text.split("```")[1].split("```")[0]
                        
                        # Parse JSON
                        generated_text = generated_text.strip()
                        parsed = json.loads(generated_text)
                        
                        st.success("Query generated successfully!")
                        st.subheader("SQL Query")
                        st.code(parsed.get("query", ""), language="sql")
                        st.subheader("Explanation")
                        st.info(parsed.get("explanation", ""))
                        
                    except json.JSONDecodeError as e:
                        st.warning("Response wasn't in perfect JSON format. Raw output:")
                        st.code(generated_text)
                else:
                    st.error("Unexpected response format")
                    st.code(json.dumps(result, indent=2))
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

st.markdown("---")
st.markdown("**Powered by Google Gemini 2.5 Flash**")