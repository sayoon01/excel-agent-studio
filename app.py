"""
Entry point — Workspace로 자동 리다이렉트
"""
import streamlit as st

st.set_page_config(page_title="AI Prompt Platform", page_icon="🤖", layout="wide")
st.switch_page("pages/2_AI_Prompt.py")
