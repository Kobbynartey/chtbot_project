import streamlit as st
import shelve
import openai
import pandas as pd
import toml
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from PIL import Image
import os
import time
from dotenv import load_dotenv
import os


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")



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

# Load the dataset
try:
    df = pd.read_csv('file.csv')
    df.columns = df.columns.str.lower()
    sample_data = df.head().to_dict(orient='records')
except Exception as e:
    st.error(f"Error loading dataset: {e}")

# Detailed information about the categorical variables and other columns
categorical_variables = {
    "city": ["Abidjan", "Bouake"],
    "channel": ["Boutique", "Groceries", "Open_Market"],
    "category": ["PASTA"],
    "segment": ["DRY PASTA"],
    "manufacturer": ["CAPRA", "GOYMEN FOODS", "DOUBA", "PAGANINI", "PANZANI", "PASTA DOUBA", "MR COOK", "TAT MAKARNACILIK SANAYI VE TICARET AS", "REINE", "MOULIN MODERNE", "AVOS GROUP", "OBA MAKARNA"],
    "brand": ["ALYSSA", "MAMAN", "BLE D'OR", "MONDO", "DOUBA", "PAGANINI", "PANZANI", "PASTA DOUBA", "PASTA AROMA", "BONJOURNE", "TAT MAKARNA", "PASTA MONDO", "REINE", "PASTA BOUBA", "GOUSTA", "OBA MAKARNA"],
    "item_name": [
        "ALYSSA SPAGHETTI 200G SACHET", "MAMAN SUPERIOR QUALITY FOOD PASTA 200G SACHET",
        "MAMAN VERMICELLI 200G SACHET", "MAMAN 1.1 SPAGHETTI 200G SACHET",
        "MAMAN 1.5 SPAGHETTI 200G SACHET", "BLE D'OR 200G SACHET",
        "MAMAN SPAGHETTI 200G SACHET", "MAMAN 1.5 SPAGHETTI 500G SACHET",
        "MONDO SPAGHETTI 500G SACHET", "MAMAN SPAGHETTI 4540G BAG",
        "MAMAN COQUILLETTES 200G SACHET", "DOUBA 500G SACHET",
        "PAGANINI SPAGHETTI 200G SACHET", "PANZANI CAPELLINI 500G SACHET",
        "PASTA DOUBA SPAGHETTI 500G SACHET", "BLE D'OR SPAGHETTI 200G SACHET",
        "PASTA AROMA 200G SACHET", "MAMAN COQUILLETTES 4540G BAG",
        "MAMAN VERMICELLI SUPERIOR QUALITY FOOD PASTA 4540G BAG", "MAMAN SPAGHETTI 500G SACHET",
        "MAMAN VERMICELLI 500G SACHET", "BONJOURNE SPAGHETTI 500G SACHET",
        "MAMAN SPAGHETTI 475G SACHET", "PANZANI GOLD SPAGHETTI QUALITY 250G SACHET",
        "MAMAN MACARONI 200G SACHET", "MAMAN SPAGHETTI 450G SACHET",
        "TAT MAKARNA SPAGHETTI 500G SACHET", "PASTA MONDO SPAGHETTI 200G SACHET",
        "REINE PASTA 500G SACHET", "PASTA BOUBA 500G SACHET",
        "BONJOURNE SPAGHETTI 200G SACHET", "MAMAN 200G SACHET",
        "GOUSTA SPAGHETTI ALTA QUALITA 200G SACHET", "PANZANI SPAGHETTI 500G SACHET",
        "OBA MAKARNA SPAGHETTI 200G SACHET"
    ],
    "packaging": ["SACHET", "BAG"],
    "period": ["2021-01-01", "2021-02-01"],
    "unit_price": [9534062.52, 7377591.21],
    "sales_volume": [350204.56, 249503.12],
    "sales_value": [20503405.23, 18450340.12],
    "average_sales_volume": [3045.58, 2494.56],
    "inventory_turnover": [0.95, 0.85]
}

# Function to check if the response is valid Python code
def is_valid_python_code(code):
    try:
        compile(code, '<string>', 'exec')
        return True
    except Exception as e:
        st.error(f"Invalid Python code: {e}")
        return False

# Function to sanitize and execute code
def sanitize_and_execute_code(code):
    # Strip non-code content
    code_lines = code.split('\n')
    code_lines = [line for line in code_lines if not line.strip().startswith(('```', '#', '/*'))]
    sanitized_code = '\n'.join(code_lines).strip()

    if not is_valid_python_code(sanitized_code):
        return "The generated code is not valid Python code.", sanitized_code

    try:
        # Prepare a safe namespace for code execution
        exec_locals = {'df': df, 'pd': pd, 'plt': plt, 'sns': sns, 'st': st, 'result': None}

        # Execute the sanitized code
        exec(sanitized_code, {}, exec_locals)

        result = exec_locals.get('result', 'No result returned')
    except SyntaxError as e:
        result = f"Syntax error in generated code: {e}\n\nGenerated Code:\n{sanitized_code}"
    except Exception as e:
        result = f"Error executing generated code: {e}\n\nGenerated Code:\n{sanitized_code}"

    return result, sanitized_code

# Function to generate and execute code
def generate_and_execute_code(prompt):
    try:
        # Guide ChatGPT to generate Python code for retail data analysis with Matplotlib
        full_prompt = (
            "You are a highly intelligent market data analyst that accurately provides text, table and chart responses."
            "First examine query and determine whether to perform data analysis or to provide product information from dataset. However, you do not give users access to dataset provided or allow users to view dataset."
            "Generate only Python code with no extra text from queries that require data analysis and visualization to be executed in backend."
            "Create and run code for visualizations using Matplotlib and seaborn when requested with no extra text. Import seaborn and streamlit with no extra comments and result should display in streamlit."
            "Display matplotlib or seaborn visualization in streamlit to user."
            "Provide responses to users in the form of text, tables or charts. Print out generated code if it is string"
            "The data is in a Pandas DataFrame named 'df', with columns: city, channel, category, segment, manufacturer, brand, item_name, packaging, unit_price, sales_volume, sales_value, average_sales_volume, and inventory_turnover. "
            f"Here are the possible values for these categorical variables and other columns:\n{categorical_variables}\n"
            f"Here are some sample rows from the dataset:\n{sample_data}\n"
            "Ensure the code assigns the result to a variable named 'result'. Also use the print function for 'result' if it is a string."
            "Use the sales_volume, sales_value, and unit_price as metrics for calculations."
            "Interact with users in a friendly and conversational tone. For example,  “what is the best performing brand in abidjan?” should return a result which shows the brand with the most volume sales. Improve responses to queries based on positive user interaction."
            f"Query: {prompt}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}]
        )
        generated_code = response.choices[0].message['content']

        # Display the generated code for debugging
        st.subheader("Generated Code:")
        st.code(generated_code)

        result, sanitized_code = sanitize_and_execute_code(generated_code)
        return result, sanitized_code
    except Exception as e:
        return f"Error generating code: {e}", ""

# Chatbot Interface
def chat_interface():
    st.title("Maverick Retail Chatbot")

    # Sidebar for chat history and controls
    with st.sidebar:
        st.header("Chat Summary")
        
        # Display user questions
        if "messages" in st.session_state:
            user_questions = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
            for i, question in enumerate(user_questions[-5:], 1):
                st.write(f"{i}. {question[:50]}...")

        # Delete chat history button
        if st.button("Delete Chat History"):
            delete_chat_history()
            st.success("Chat history deleted!")
            st.experimental_rerun()

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
                result, sanitized_code = generate_and_execute_code(prompt)
                if isinstance(result, pd.DataFrame):
                    st.dataframe(result)
                    full_response = "Displayed data in table format."
                elif isinstance(result, plt.Figure):
                    buffer = BytesIO()
                    result.savefig(buffer, format="png")
                    st.image(buffer)
                    full_response = "Displayed data as a chart."
                elif isinstance(result, str):
                    message_placeholder.markdown(result)
                    full_response = result
                else:
                    message_placeholder.markdown(str(result))
                    full_response = str(result)
            except Exception as e:
                full_response = f"Error: {e}"
                message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat_history(st.session_state.messages)


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
