import streamlit as st
import os

st.write("# Hello world!")
st.write(f"env var: {os.environ.get('var')}")
st.write(f"st secret var: {st.secrets['var']}")

st.text_input("Input you text", key="first_text")

st.write(st.session_state.first_text)
