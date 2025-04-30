import streamlit as st
from utils.agent_helpers import query_race_agent
#from theme_utils import apply_theme

# 1) Page config + theme
st.set_page_config(page_title="Chatbot | 10K Documents", page_icon="💵", layout="wide")
#apply_theme()

# 2) Initialize chat history in session_state
if "chat_history" not in st.session_state:
    # each entry is dict(role="user"/"assistant", "message": str)
    st.session_state.chat_history = []

if "trace" not in st.session_state:
    st.session_state.trace = None

# 3) Layout
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("### 🗣️ Ask a Question")
    
    # 4) Replay the history
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["message"])

    # 5) Input box
    user_question = st.chat_input("Type your question about publicly traded equities from 2024…")

    if user_question:
        # 6) Append user message
        st.session_state.chat_history.append({"role": "user", "message": user_question})
        try:
            # 7) Generate assistant response
            response, trace = query_race_agent(user_question)
        except Exception as e:
            response = f"⚠️ Error: {e}"
            trace = None

        # 8) Append assistant message
        st.session_state.chat_history.append({"role": "assistant", "message": response})
        st.session_state.trace = trace

        # 9) Rerun so the new messages show up in the loop above
        st.rerun()

with col2:
    st.markdown("### 🧾 Traceability")
    if st.session_state.trace:
        st.info("Click below for traceability chunks")
        @st.dialog("Traceability")
        def show_trace():
            trace = st.session_state.trace
            if isinstance(trace, list):
                for i, item in enumerate(trace):
                    st.markdown(f"**Source {i+1}:** {item.get('source','?')}")
            else:
                st.markdown(str(trace))
        if st.button("Traceability"):
            show_trace()
    else:
        st.button("Traceability", disabled=True)
