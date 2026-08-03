import voyageai
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
voyage_api_key = os.getenv("VOYAGE_API_KEY")
database_url = os.getenv("DATABASE_URL")

vo = voyageai.Client()

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

texts = [chunk[0] for chunk in chunks_list]

response = vo.embed(
    texts=texts ,
    model="voyage-3.5-lite" ,
    input_type="document"
)

result_embeddings = response.embeddings

with psycopg2.connect(database_url) as conn:
    with conn.cursor() as cur:
        for (text, origin), embedding in zip(chunks_list, result_embeddings):
            cur.execute("INSERT INTO document_chunks (content, source_document, embedding) VALUES (%s, %s, %s);", (text, origin, embedding,))

        conn.commit()

print(f"{len(chunks_list)} chunks inseridos com sucesso.")