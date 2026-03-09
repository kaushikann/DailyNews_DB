import streamlit as st
import os
import asyncio

from openai import OpenAI
from composio import Composio
from composio_openai import OpenAIProvider
from agents import Agent, Runner, WebSearchTool
from supabase import create_client

supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

supabase = create_client(supabase_url, supabase_key)

async def News_Tool():
    agent = Agent(
        name="Assistant",
        tools=[WebSearchTool()],
        instructions=(
            "You are a helpful assistant who collects news from the internet "
            "from reliable sources and summarizes them."
        ),
    )
    result1 = await Runner.run(
        agent,
        (
            "What is the latest news about AI? Give a brief summary in 100 words "
            "for each news. Only give me news in the last 72 hours. Always quote "
            "the source and date of the news."
        ),
    )
    return result1.final_output


def Email_Tool(news, email):
    composio = Composio(
        api_key=st.secrets["COMPOSIO_API_KEY"],
        provider=OpenAIProvider(),
    )
    openai_client = OpenAI()

    tools = composio.tools.get(
        user_id=st.secrets["USERID"],
        tools=["GMAIL_SEND_EMAIL"]
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        tools=tools,
        messages=[
            {"role": "system", "content": "You are an assistant that sends emails."},
            {"role": "user", "content": f"Send an email to {email} with subject 'Daily AI News' and body: {news}"},
        ],
    )

    result = composio.provider.handle_tool_calls(response=response, user_id=st.secrets["USERID"])
    return result
    
st.header(":blue[Daily AI News]")

if "news" not in st.session_state:
    st.session_state["news"] = ""

if st.button("What's the recent news about AI?", type="primary"):
    with st.spinner("Fetching news..."):
        news = asyncio.run(News_Tool())
        st.session_state["news"] = news
        st.success("News fetched!")
        st.text_area("Latest AI News", st.session_state["news"], height=300)


if st.session_state["news"]:
    st.write(
        "Give your email address to send this news to your inbox. "
        "This will be a one-time email and not a recurring one. "
        "We do not store your email address!"
    )
    email = st.text_input("Enter your email")
    if st.button("Send this news via Email"):
        if email:
            with st.spinner("Sending email..."):
                try:
                    result = Email_Tool(st.session_state["news"], email)
                    if result:
                        st.success("Email sent successfully!")
                        data = {"Email": email}

                        response = supabase.table("UserInformation").insert(data).execute()
                        response = supabase.table("UserInformation").select("*").execute()
                        st.write(response.data)
                    else:
                        st.warning("Something went wrong")
                except Exception as e:
                    st.error(f"Failed to send email: {e}")
        else:
            st.warning("Please fetch the news first.")















