import streamlit as st


class CSSManipulator:
    def __init__(self):
        self.styles = []

    def add_style(self, styles_dict):
        style_content = ""
        for class_name, css_input in styles_dict.items():
            style_content += f"{class_name} {{ {css_input}; }}\n"
        style = f"""
            <style>
              {style_content}
            </style>
        """
        st.html(style)
