import voyageai
import os
from dotenv import load_dotenv

load_dotenv()
voyage_api_key = os.getenv("VOYAGE_API_KEY")


with open("README.md", "r", encoding="utf-8") as readme_file:
    readme_content = readme_file.read()
    
with open("HANDOFF.md", "r", encoding="utf-8") as handoff_file:
    handoff_content = handoff_file.read()
    
readme_chunks = readme_content.split("## ")
readme_chunks = readme_chunks[1:]

handoff_chunks = handoff_content.split("## ")
handoff_chunks = handoff_chunks[1:]

chunks_list = []

for chunk in readme_chunks:
    chunk_content = (chunk, "README")
    chunks_list.append(chunk_content)

for chunk in handoff_chunks:
    chunk_content = (chunk, "HANDOFF")
    chunks_list.append(chunk_content)