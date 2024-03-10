import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import os
import webbrowser
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

def init():
    load_dotenv()

    if os.getenv("OPENAI_API_KEY") is None or os.getenv("OPENAI_API_KEY") == "":
        print("OPENAI_API_KEY is not set")
        exit(1)
    else:
        print("OPENAI_API_KEY is set")

    st.set_page_config(
        page_title="IntelliChat",
        page_icon="🤖"
    )

def redirect_to_domain(domain_name):
    website_url = f"https://{domain_name}.com"
    st.success(f"Redirecting to: {website_url}")
    webbrowser.open_new_tab(website_url)

def scroll_to_top():
    """Scrolls to the top of the page."""
    js_code = """
    <script>
        var body = window.parent.document.querySelector(".main");
        body.scrollTop = 0;
    </script>
    """
    st.components.v1.html(js_code)

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

    # Add a button to go back to the top
    st.button("Back to Top", on_click=scroll_to_top)

if __name__ == '__main__':
    main()
