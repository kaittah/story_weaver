import streamlit as st

from src.utils.llm import Anthropic, OpenAI

if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = ""
if "anthropic_api_key" not in st.session_state:
    st.session_state["anthropic_api_key"] = ""
if "vendor" not in st.session_state:
    st.session_state["vendor"] = None
if "model_name" not in st.session_state:
    st.session_state["model_name"] = "default"


vendor_name = st.selectbox("Select a vendor", ["openai", "anthropic"])
model_name = st.text_input("(Optional) Enter a model name", "default")
if vendor_name == "anthropic":
    anthropic_api_key =  st.session_state["anthropic_api_key"]
    if model_name != "default":
        vendor = Anthropic(api_key=anthropic_api_key, default_model_name=model_name)
    else:
        vendor = Anthropic(api_key=anthropic_api_key)
    st.session_state["vendor"] = vendor
else:
    openai_api_key = st.session_state["openai_api_key"]
    if model_name != "default":
        vendor = OpenAI(api_key=openai_api_key, default_model_name=model_name)
    else:
        vendor = OpenAI(api_key=openai_api_key)
    st.session_state["openai_api_key"] = openai_api_key
    st.session_state["vendor"] = vendor

st.session_state["vendor"] = vendor
st.session_state["model_name"] = model_name

