import streamlit as st
from dotenv import load_dotenv
import os
import webbrowser
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
from streamlit_chat import message
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
 
def back_to_top():
    """Scrolls to the top of the page."""
    js_code = """
<script>
        var body = window.parent.document.querySelector(".main");
        body.scrollTop = 0;
</script>
    """
    st.components.v1.html(js_code)
 
def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
 
    init()
 
    st.header(" WELCOME TO INTELLICHAT 🤖")
 
    chat = ChatOpenAI(temperature=0)  # Initialize chat object
 
    # Sidebar with user input
    with st.sidebar:
        user_input = st.text_input("Your message: ", key="user_input")
 
        # Upload PDF file
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf_file:
            # Summarize the PDF
            pdf_summary = summarize_pdf(pdf_file.read())
            st.info("Summary of the PDF:")
            st.write(pdf_summary)  # Display the summary
 
    # Handle user input
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        if user_input.startswith(('http://', 'https://')):
            st.success(f"Redirecting to: {user_input}")
            webbrowser.open_new_tab(user_input)
        elif "redirect me to" in user_input.lower():
            # Extract the domain name from the user input
            domain_name = user_input.lower().split("redirect me to", 1)[1].strip()
            redirect_to_domain(domain_name)
        else:
            with st.spinner("Wait..."):
                response = chat(st.session_state.messages)  # Pass only the current message
            st.session_state.messages.append(AIMessage(content=response.content))
 
    # Display message history
    messages = st.session_state.get('messages', [])
    for i, msg in enumerate(messages):
        if i % 2 == 0:
            message(msg.content, is_user=True, key=str(i) + '_user')
        else:
            message(msg.content, is_user=False, key=str(i) + '_ai')
 
    # Add a button to go back to the top
    st.sidebar.button("Back to Top", on_click=back_to_top)
 
    if pdf_file:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
 
        # split into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
 
        # create embeddings
        embeddings = OpenAIEmbeddings()
        knowledge_base = FAISS.from_texts(chunks, embeddings)
 
        # show user input
        user_question = st.text_input("Ask a question about your PDF:")
        if user_question:
            docs = knowledge_base.similarity_search(user_question)
 
            llm = OpenAI()
            chain = load_qa_chain(llm, chain_type="stuff")
            with get_openai_callback() as cb:
                response = chain.run(input_documents=docs, question=user_question)
                print(cb)
 
            st.write(response)
 
if __name__ == '__main__':
    main()
