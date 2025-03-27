import streamlit as st
import os
import sys

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the enhanced mortgage assistant
from mortgage_assistant_bp2 import ConversationalMortgageAgent

def initialize_chat():
    """Initialize chat session and welcome message"""
    if 'mortgage_agent' not in st.session_state:
        st.session_state['mortgage_agent'] = ConversationalMortgageAgent()
        welcome_msg = "Hello! I'm your mortgage advisor. I'm here to help you find the right mortgage solution tailored to your needs. Are you looking to buy your first home, refinance, or invest in property?"
        st.session_state['messages'] = [{"role": "assistant", "content": welcome_msg}]

def main():
    st.set_page_config(
        page_title="AI Mortgage Advisor",
        page_icon="🏠",
        layout="centered"
    )

    # Apply custom styling
    st.markdown("""
        <style>
        .stApp {background-color: #f5f7f9;}
        div.stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .user-message {background-color: #e3f2fd;}
        .assistant-message {background-color: white;}
        h1 {color: #1e3a8a;}
        .stChatInputContainer {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: white;
        }
        .css-1rin5o2 {
            padding: 15px;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display bank logo or advisory banner
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏠 Personalized Mortgage Assistant")
        st.markdown("*Personalized mortgage offers for your unique needs*")
    
    # Display debug info if in debug mode
    if 'debug_mode' not in st.session_state:
        st.session_state['debug_mode'] = False
        
    if st.session_state['debug_mode']:
        with st.expander("Debug Information", expanded=False):
            if 'mortgage_agent' in st.session_state:
                st.write("Current Stage:", st.session_state['mortgage_agent'].state['conversation_stage'])
                st.write("Steps Completed:", st.session_state['mortgage_agent'].state['steps_completed'])
                st.write("Collected Info:", st.session_state['mortgage_agent'].state['collected_info'])
                st.write("Serviceability Metrics:", st.session_state['mortgage_agent'].state['serviceability_metrics'])
    
    # Initialize chat
    initialize_chat()
    
    # Create container for chat history
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.markdown(f"<div class='{message['role']}-message'>{message['content']}</div>", 
                           unsafe_allow_html=True)

    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(f"<div class='user-message'>{user_input}</div>", 
                       unsafe_allow_html=True)
        
        # Display thinking message
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown("<div class='assistant-message'>Analyzing your situation...</div>", unsafe_allow_html=True)
        
        # Get response from agent
        agent = st.session_state['mortgage_agent']
        response = agent.get_next_response(user_input)
        
        # Update with actual response
        with st.chat_message("assistant"):
            thinking_placeholder.markdown(f"<div class='assistant-message'>{response}</div>", 
                           unsafe_allow_html=True)
        
        # Add messages to chat history
        st.session_state['messages'].extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])
        
        # Auto-scroll to bottom
        js = '''
        <script>
            function scrollToBottom() {
                const messages = document.querySelectorAll('.stChatMessage');
                if (messages) {
                    const lastMessage = messages[messages.length - 1];
                    if (lastMessage) {
                        lastMessage.scrollIntoView();
                    }
                }
            }
            setTimeout(scrollToBottom, 100);
        </script>
        '''
        st.components.v1.html(js, height=0)

if __name__ == "__main__":
    main()