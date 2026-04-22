import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
load_dotenv()

conn_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING")

blob_service_client=BlobServiceClient.from_connection_string(conn_str)
blob_client=blob_service_client.get_blob_client(
  container="scrappeddata",
  blob="infinito_dedup.txt"
)
text_bytes=blob_client.download_blob().readall()
text =text_bytes.decode("utf-8")

#CHUNKING 
def chunk_text(text,size=200):
  words=text.split()
  return[" ".join(words[i:i+size]) for i  in range(0,len(words),size)]
chunks=chunk_text(text)
print(len(chunks))
print(chunks[0])

#EMBEDDINGS
client= AzureOpenAI(
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
   api_version="2024-02-15-preview",
   azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")  
)
response=client.embeddings.create(
  model="embedding_model",
  input=chunks
)
print(len(chunks))
print(len(response.data))

#DOCUMENT FOR AI SEARCH
documents=[]
for i, chunk in enumerate(chunks):
  documents.append({
    "id":str(i),
    "content":chunk,
    "contentVector":response.data[i].embedding
  })
print(documents[0])

#ADDING TO AI SEARCH

search_client=SearchClient(
  endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
  index_name="infinito-index",
  credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))

)
result=search_client.upload_documents(documents)
print(result)


results=search_client.search(
  search_text="finance solution",
  top=3
)
for r in results:
  print(r['content'])