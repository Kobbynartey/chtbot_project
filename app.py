import streamlit as st
import shelve
from config import API_KEY
import openai

# Ensure openai_model is initialized in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"
try:
    import openai
    openai.api_key = API_KEY
except ImportError:
    st.error("OpenAI library is not installed. Please install it using 'pip install openai'")



# Load chat history from shelve file
def load_chat_history():
    try:
        with shelve.open("chat_history") as db:
            return db.get("messages", [])
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        return []

# Save chat history to shelve file
def save_chat_history(messages):
    try:
        with shelve.open("chat_history") as db:
            db["messages"] = messages
    except Exception as e:
        st.error(f"Error saving chat history: {e}")

# Delete chat history
def delete_chat_history():
    try:
        with shelve.open("chat_history") as db:
            if "messages" in db:
                del db["messages"]
        st.session_state.messages = []
    except Exception as e:
        st.error(f"Error deleting chat history: {e}")

def chat_interface():
    st.title("Mav Chatbot Interface")

    # Sidebar
    with st.sidebar:
        st.header("Chat Summary")
        
        # Display user questions
        if "messages" in st.session_state:
            user_questions = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
            for i, question in enumerate(user_questions[-5:], 1):  # Display last 5 questions
                st.write(f"{i}. {question[:50]}...")  # Truncate long questions
        
        # Delete chat history button
        if st.button("Delete Chat History"):
            delete_chat_history()
            st.success("Chat history deleted!")
            st.rerun()

    # Main chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything about our retail data?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                ):
                    full_response += response.choices[0].delta.get("content", "")
                    message_placeholder.markdown(full_response + "▌")
            except NameError:
                full_response = "Error: OpenAI library is not available. Please install it to use this feature."
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat_history(st.session_state.messages)

# This is not necessary if you're running the app from auth.py
# if __name__ == "__main__":
#     chat_interface()