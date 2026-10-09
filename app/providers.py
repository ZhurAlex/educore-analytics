from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent

async def make_request_to_LLM(message, system_prompt, response_model):
    gemini = ChatGoogleGenerativeAI(model="gemini-3.8-flash").with_structured_output(response_model)
    mistral = ChatMistralAI(model="mistral-small-latest").with_structured_output(response_model)
    openai = ChatOpenAI(model="gpt-5-mini").with_structured_output(response_model)

    model = gemini.with_fallbacks([mistral, openai])

    return await model.ainvoke([SystemMessage(system_prompt), HumanMessage(message)])

