from dotenv import load_dotenv
from langchain.messages import HumanMessage
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from models import ChapterIndex
from pathlib import Path
import base64
import json

load_dotenv()

def get_files_list(folder):
    folder_path = Path(folder)
    return sorted([f.name for f in folder_path.iterdir() if f.is_file()])

def get_file(filepath):
    with open(filepath, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
    return pdf_b64

def build_agent():
    return create_agent(model='gpt-5-mini',
                     system_prompt="You are analyzing pages from an English grammar workbook.",
                     response_format=ChapterIndex)

def build_gemini_agent():
    model = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

    return create_agent(
        model=model,
        system_prompt="You are analyzing pages from an English grammar workbook.",
        response_format=ChapterIndex,
    )

def convert_text_to_models(agent, file, filename):
    question = HumanMessage(content=[
        {"type": "text", "text": "Go through every page of this chapter and extract every exercise you find, following the schema."},
        {"type": "file", "base64": file, "mime_type": "application/pdf", "filename": filename}
    ])

    response = agent.invoke({"messages": [question]})
    result = response["structured_response"]
    result.source_file = filename
    return result

def convert_data_to_json(data, output_path="index.json"):
    path = Path(output_path)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    existing.append(data.model_dump(mode="json"))
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

def already_processed(output_path="index.json"):
    path = Path(output_path)
    if not path.exists():
        return set()
    return {entry["source_file"] for entry in json.loads(path.read_text(encoding="utf-8"))}

filepath = "data/textbooks/english/grammatika_golitsynskiy_chapters"
files = get_files_list(filepath)

done = already_processed()

# agent = build_agent()
agent = build_gemini_agent()

for filename in files:
    if filename in done:
        print(f"Skipping {filename}, already processed")
        continue
    try:
        pdf_b64 = get_file(f"{filepath}/{filename}")
        response = convert_text_to_models(agent, pdf_b64, filename)
        convert_data_to_json(response)
        print(f"Processed {filename} and saved to index.json")
    except Exception as e:
        print(f"Failed on {filename}: {e}")
        continue