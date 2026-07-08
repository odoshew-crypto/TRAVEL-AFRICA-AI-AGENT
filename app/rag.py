import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="app/chroma_db")
collection = client.get_or_create_collection(name="travel_africa_hotels")


def create_embeddings():
    df = pd.read_csv("app/data/hotels.csv")

    if df.empty:
        return {"message": "No hotel data found"}

    for index, row in df.iterrows():
        text = f"""
        Hotel Name: {row['hotel_name']}
        Location: {row['location']}
        Country: {row['country']}
        Description: {row['description']}
        Amenities: {row['amenities']}
        Rating: {row['rating']}
        Website: {row['website_url']}
        Source: {row['source_url']}
        """

        embedding = model.encode(text).tolist()

        collection.upsert(
            ids=[str(index)],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                "hotel_name": str(row["hotel_name"]),
                "location": str(row["location"]),
                "source_url": str(row["source_url"])
            }]
        )

    return {
        "message": "Embeddings created successfully",
        "records": len(df)
    }


def ask_question(question: str):
    question_embedding = model.encode(question).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=5
    )

    if not results["documents"] or not results["documents"][0]:
        return {
            "answer": "No matching hotel information found. Please create embeddings first.",
            "sources": []
        }

    metas = results["metadatas"][0]

    answer = "Based on the hotel data, here are good options:\n\n"

    for meta in metas:
        answer += f"- {meta['hotel_name']} in {meta['location']}\n"

    return {
        "answer": answer,
        "sources": metas
    }