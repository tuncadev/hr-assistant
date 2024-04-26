import streamlit as st

first = st.text_input("What is your name? ")
if first:
    st.write(f"Your name is '{first}'")



