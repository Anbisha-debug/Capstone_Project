import streamlit as st
from agent import StockAgent
from logger_config import setup_logger

logger = setup_logger('main')

def main():
    st.set_page_config(page_title="Stock Market Agent", page_icon="📈")
    st.title("📈 Stock Market Analysis Agent")

    if "agent" not in st.session_state:
        st.session_state.agent = StockAgent()

    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about stocks..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            response = st.session_state.agent.process_query(prompt)
        
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
