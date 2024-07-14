import streamlit as st
from PIL import Image
import os
import time
from app import chat_interface

# Set page config at the very beginning
st.set_page_config(page_title="Maverick Chatbot")

# CSS styles
css = """
<style>
body {
    font-family: Arial, sans-serif;
}
.stButton > button {
    width: 100%;
    border-radius: 20px;
    background-color: #FF4B4B;
    color: white;
    border: none;
    padding: 10px 0;
}
.centered {
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
"""

def welcome_page():
    st.markdown("<h1 style='text-align: center;'>Maverick Chatbot</h1>", unsafe_allow_html=True)
    
    # Create a placeholder for the animated text
    text_placeholder = st.empty()
    
    image_path = "get_started.png"
    
    if os.path.exists(image_path):
        image = Image.open(image_path)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image(image, width=300, use_column_width=True)
    else:
        st.error(f"Image not found at path: {image_path}")
    
    if st.button("Get Started"):
        st.session_state.page = 'chat'
        st.rerun()

    # List of phrases to animate
    phrases = [
        "Instant Retail Savvy, Just Ask!",
        "Retail Insights on Demand!",
        "Effortless Retail Intelligence!"
    ]
    
    # Animation loop
    for phrase in phrases:
        for i in range(len(phrase) + 1):
            text_placeholder.markdown(f"<h2 style='text-align: center; color: #FF4B4B;'>{phrase[:i]}▌</h2>", unsafe_allow_html=True)
            time.sleep(0.05)
        time.sleep(1)  # Pause at the end of each phrase

def auth_main():
    st.markdown(css, unsafe_allow_html=True)

    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'

    if st.session_state.page == 'welcome':
        welcome_page()
    elif st.session_state.page == 'chat':
        chat_interface()

if __name__ == "__main__":
    auth_main()