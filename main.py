import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import os
import webbrowser
import fitz  # PyMuPDF
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

def init():
    # Load the OpenAI API key from the environment variable
    load_dotenv()

    # Test that the API key exists
    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        print("OPENAI_API_KEY is not set")
        exit(1)
    else:
        print("OPENAI_API_KEY is set")

    # Setup Streamlit page
    st.set_page_config(
        page_title="IntelliChat",
        page_icon="🤖"
    )

def redirect_to_domain(domain_name):
    # Generate a URL with the specified domain name
    website_url = f"https://{domain_name}.com"
    st.success(f"Redirecting to: {website_url}")
    webbrowser.open_new_tab(website_url)

def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()
    return text

def summarize_pdf(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page_num in range(min(3, doc.page_count)):  # Extract first 3 pages for summary
            page = doc[page_num]
            text += page.get_text("text")
        return text
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return None

def main():
    init()

    chat = ChatOpenAI(temperature=0)

    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="You are a helpful assistant.")
        ]

    st.header(" WELCOME TO INTELLICHAT 🤖")

    # Sidebar with user input
    with st.sidebar:
        user_input = st.text_input("Your message: ", key="user_input")

        # Upload PDF file
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            pdf_text = extract_text_from_pdf(pdf_file.read())
            user_input += "\n" + pdf_text

            # Summarize the PDF
            pdf_summary = summarize_pdf(pdf_file.read())
            st.info("PDF Summary:")
            st.write(pdf_summary)

    # Handle user input
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))

        # Check if the user input is a URL
        if user_input.startswith(('http://', 'https://')):
            st.success(f"Redirecting to: {user_input}")
            webbrowser.open_new_tab(user_input)
        elif "redirect me to" in user_input.lower():
            # Extract the domain name from the user input
            domain_name = user_input.lower().split("redirect me to", 1)[1].strip()
            redirect_to_domain(domain_name)
        else:
            with st.spinner("Wait..."):
                response = chat(st.session_state.messages)
            st.session_state.messages.append(AIMessage(content=response.content))

    # Display message history
    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages[1:]):
        if i % 2 == 0:
            message(msg.content, is_user=True, key=str(i) + '_user')
        else:
            message(msg.content, is_user=False, key=str(i) + '_ai')

if __name__ == '__main__':
    main()
