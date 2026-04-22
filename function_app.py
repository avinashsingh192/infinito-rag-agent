import azure.functions as func
import os
from openai import AzureOpenAI
import requests

app = func.FunctionApp()

# 🔹 single client (don’t recreate repeatedly)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


def get_query_embedding(query):
    response = client.embeddings.create(
        model="embedding_model",
        input=query
    )
    return response.data[0].embedding


def search_similar_chunks(query_embedding):
    url = f"{os.getenv('AZURE_SEARCH_ENDPOINT')}/indexes/infinito-index/docs/search?api-version=2024-03-01-Preview"

    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("AZURE_SEARCH_KEY")
    }

    body = {
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": query_embedding,
                "fields": "contentVector",
                "k": 5
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    data = response.json()

    return [doc.get("content", "") for doc in data.get("value", [])]


@app.route(route="infinit_o_agent", auth_level=func.AuthLevel.ANONYMOUS)
def infinit_o_agent(req: func.HttpRequest) -> func.HttpResponse:

    query = req.params.get("q")
    if not query:
        return func.HttpResponse("Missing query", status_code=400)

    # 🔹 pipeline
    embedding = get_query_embedding(query)
    chunks = search_similar_chunks(embedding)
    context = "\n\n".join(chunks)

    response = client.chat.completions.create(
        model="infinit-o-analyst",
        messages=[
            {
                "role": "system",
                "content": "Answer using the provided context. If not found, say 'Not found in context.'"
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}"
            }
        ]
    )

    answer = response.choices[0].message.content

    return func.HttpResponse(answer)