import os
from pinecone import Pinecone, ServerlessSpec, VectorType
from app.services.openai_service import get_embedding

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENV = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1-aws")  # update if needed

EMBEDDING_DIMENSION = 1536

# Initialize client
pc = Pinecone(api_key=PINECONE_API_KEY)

def embed_chunks_and_upload_to_pinecone(chunks: list[str], index_name: str, namespace: str = ""):
    # If exists, delete index
    existing = pc.list_indexes()
    if index_name in existing:
        print(f"\nIndex '{index_name}' already exists. Deleting …")
        pc.delete_index(name=index_name)
    # Create index: serverless spec
    print(f"\nCreating new index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        vector_type=VectorType.DENSE,
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    # Get index handle
    idx = pc.Index(name=index_name)
    # Embed chunks and upload in batch
    print("\nEmbedding chunks …")
    vectors = []
    for i, chunk in enumerate(chunks):
        vec = get_embedding(chunk)
        vectors.append((str(i), vec, {"chunk_text": chunk}))
    print(f"Uploading {len(vectors)} vectors …")
    idx.upsert(vectors=vectors, namespace=namespace)
    print(f"Uploaded {len(vectors)} chunks to index '{index_name}' (namespace='{namespace}').")

def get_most_similar_chunks_for_query(query: str, index_name: str, top_k: int = 3, namespace: str = "") -> list[str]:
    print("\nEmbedding query …")
    q_vec = get_embedding(query)
    idx = pc.Index(name=index_name)
    print("Querying Pinecone index …")
    resp = idx.query(
        vector=q_vec,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True
    )
    chunks = [match["metadata"]["chunk_text"] for match in resp["matches"]]
    return chunks

def delete_index(index_name: str):
    existing = pc.list_indexes()
    if index_name in existing:
        print(f"\nDeleting index '{index_name}' …")
        pc.delete_index(name=index_name)
        print(f"Index '{index_name}' deleted.")
    else:
        print(f"\nIndex '{index_name}' does not exist — nothing to delete.")
