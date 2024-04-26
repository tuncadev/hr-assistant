import os
import uuid
import streamlit as st


def get_temp_path():
    if 'temp_path' not in st.session_state:
        temp_name = str(uuid.uuid4())
        temp_path = f"temp/{temp_name}"
        os.makedirs(temp_path, exist_ok=True)
        st.session_state['temp_path'] = temp_path
    return st.session_state['temp_path']


name = st.text_input("Enter your name")
temp_path = get_temp_path()
with open(os.path.join(temp_path, "first_analysis.txt"), "w") as f:
    f.write(name)

