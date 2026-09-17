import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client, Client
import os
import time

logo_path = "logo.png" if os.path.exists("logo.png") else "✍️"
st.set_page_config(page_title="LyzAI", page_icon=logo_path if os.path.exists("logo.png") else "✍️", layout="wide")

# Etiqueta de verificación para Google Search Console
st.markdown('<meta name="google-site-verification" content="eVD2UKFxTlBqnLiLxQQbRxdlUMBbqpjwA7z7toKBXCg" />', unsafe_allow_html=True)

# ==========================================
# CONFIGURACIÓN SEGURA (SECRETS DE STREAMLIT)
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

def get_supabase_client() -> Client:
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state.supabase_client

def get_genai_client():
    if "genai_client" not in st.session_state:
        st.session_state.genai_client = genai.Client(api_key=GEMINI_API_KEY)
    return st.session_state.genai_client
