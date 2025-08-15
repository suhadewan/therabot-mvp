from collections import defaultdict
from datetime import datetime, timedelta

import openai
import streamlit as st

from config import config
from guardrails import regenerate_if_needed
from moderation import moderate_content
from crisis_detection import detect_crisis_keywords
from llm_safety_check import analyze_content_with_llm, get_llm_detected_response

st.set_page_config(
    page_title=config.PAGE_TITLE, page_icon=config.PAGE_ICON, layout=config.PAGE_LAYOUT
)

st.markdown(config.SAFETY_BANNER_HTML, unsafe_allow_html=True)

st.title(config.APP_TITLE)
st.caption(config.APP_CAPTION)

# Add crisis hotlines to sidebar
with st.sidebar:
    st.markdown("### 📞 Emergency Helplines")
    st.markdown(config.CRISIS_HOTLINES_HTML, unsafe_allow_html=True)
    
    # Add some spacing and additional resources
    # st.markdown("---")
    st.markdown("### 🆘 In Crisis?")
    st.markdown("""
    - **Emergency Services**: 112
    - **Police**: 100
    - **Ambulance**: 102
    """)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "rate_limit" not in st.session_state:
    st.session_state.rate_limit = defaultdict(list)


def check_rate_limit(ip_address="default"):
    """Check if user has exceeded rate limit"""
    current_time = datetime.now()
    hour_ago = current_time - timedelta(hours=config.RATE_LIMIT_WINDOW_HOURS)

    st.session_state.rate_limit[ip_address] = [
        timestamp
        for timestamp in st.session_state.rate_limit[ip_address]
        if timestamp > hour_ago
    ]

    if len(st.session_state.rate_limit[ip_address]) >= config.RATE_LIMIT_REQUESTS:
        return False

    st.session_state.rate_limit[ip_address].append(current_time)
    return True


def load_system_prompt():
    """Load system prompt from file"""
    try:
        with open(config.SYSTEM_PROMPT_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return """You are a supportive mental health companion for youth.
        Be empathetic, non-judgmental, and encouraging.
        Keep responses under 50 words and end with a follow-up question."""


# Check for API key before initializing client
if "OPENAI_API_KEY" not in st.secrets:
    st.error(config.ERROR_API_KEY)
    st.info(
        "Go to your app settings on Streamlit Cloud and add:\n"
        "- Key: `OPENAI_API_KEY`\n"
        "- Value: Your OpenAI API key"
    )
    st.stop()

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input(config.CHAT_PLACEHOLDER):
    if not check_rate_limit():
        st.error(config.ERROR_RATE_LIMIT)
    else:
        # Check for crisis keywords first
        is_crisis, crisis_response = detect_crisis_keywords(prompt)
        
        if is_crisis:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                st.warning("🚨 Crisis detected - Immediate support resources:")
                st.markdown(crisis_response)
            
            st.session_state.messages.append(
                {"role": "assistant", "content": crisis_response}
            )
        else:
            # Additional LLM-based safety check for nuanced detection
            is_llm_concerning, concern_type, analysis = analyze_content_with_llm(prompt, client)
            
            if is_llm_concerning:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                with st.chat_message("assistant"):
                    st.warning(f"⚠️ Safety concern detected - Support available:")
                    llm_response = get_llm_detected_response(concern_type, analysis)
                    st.markdown(llm_response)
                    
                    # Show analysis details in expander for transparency
                    with st.expander("🔍 Analysis Details"):
                        st.json(analysis)
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": llm_response}
                )
            else:
                # Normal flow - moderation and chat
                is_safe, moderation_result = moderate_content(prompt, client)

                if not is_safe:
                    st.error(config.ERROR_MODERATION)
                else:
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.write(prompt)

                    messages = [
                        {"role": "system", "content": load_system_prompt()}
                    ] + st.session_state.messages

                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        full_response = ""

                        try:
                            stream = client.chat.completions.create(
                                model=config.MODEL_NAME,
                                messages=messages,
                                temperature=config.MODEL_TEMPERATURE,
                                max_tokens=config.MODEL_MAX_TOKENS,
                                stream=config.MODEL_STREAM,
                            )

                            for chunk in stream:
                                if chunk.choices[0].delta.content is not None:
                                    full_response += chunk.choices[0].delta.content
                                    message_placeholder.markdown(full_response + "▌")

                            final_response = regenerate_if_needed(
                                full_response, messages, client
                            )

                            message_placeholder.markdown(final_response)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": final_response}
                            )

                        except Exception as e:
                            st.error(config.ERROR_GENERIC.format(error=str(e)))
