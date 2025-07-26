from collections import defaultdict
from datetime import datetime, timedelta

import openai
import streamlit as st

from guardrails import regenerate_if_needed
from moderation import moderate_content

st.set_page_config(
    page_title="Mental Health Support Bot", page_icon="🧠", layout="centered"
)

st.markdown(
    """
<div style='background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem;
margin-bottom: 1rem;'>
⚠️ <strong>Important Notice</strong>: This is a non-clinical support tool for
general mental wellness. If you're experiencing a crisis, please contact
emergency services (911) or a crisis hotline immediately.
</div>
""",
    unsafe_allow_html=True,
)

st.title("Mental Health Support Bot 🧠")
st.caption("A supportive companion for youth mental wellness")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "rate_limit" not in st.session_state:
    st.session_state.rate_limit = defaultdict(list)


def check_rate_limit(ip_address="default"):
    """Check if user has exceeded rate limit (20 requests per hour)"""
    current_time = datetime.now()
    hour_ago = current_time - timedelta(hours=1)

    st.session_state.rate_limit[ip_address] = [
        timestamp
        for timestamp in st.session_state.rate_limit[ip_address]
        if timestamp > hour_ago
    ]

    if len(st.session_state.rate_limit[ip_address]) >= 20:
        return False

    st.session_state.rate_limit[ip_address].append(current_time)
    return True


def load_system_prompt():
    """Load system prompt from file"""
    try:
        with open("system_prompt.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return """You are a supportive mental health companion for youth.
        Be empathetic, non-judgmental, and encouraging.
        Keep responses under 50 words and end with a follow-up question."""


# Check for API key before initializing client
if "OPENAI_API_KEY" not in st.secrets:
    st.error("⚠️ OpenAI API key not found. Please add it to Streamlit Cloud secrets.")
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

if prompt := st.chat_input("How are you feeling today?"):
    if not check_rate_limit():
        st.error(
            "You've reached the hourly message limit (20). Please try again later."
        )
    else:
        is_safe, moderation_result = moderate_content(prompt, client)

        if not is_safe:
            st.error(
                "I noticed your message might contain sensitive content. "
                "Let's focus on constructive support."
            )
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
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=100,
                        stream=True,
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
                    st.error(f"An error occurred: {str(e)}")
