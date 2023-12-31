from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from sklearn.cluster import KMeans
import numpy as np
from kneed import KneeLocator
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

def split_and_embed_text(text, openai_api_key):
    try:
        text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\t"], chunk_size=10000, chunk_overlap=3000)
        docs = text_splitter.create_documents([text])
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectors = embeddings.embed_documents([x.page_content for x in docs])
        return docs, vectors
    except Exception as e:
        logging.error(f"Error during text splitting and embedding: {e}")
        raise

def determine_optimal_clusters(vectors, max_clusters=100):
    sse = []
    for k in range(1, max_clusters + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(vectors)
        sse.append(kmeans.inertia_)
    elbow_point = KneeLocator(range(1, len(sse) + 1), sse, curve='convex', direction='decreasing').elbow
    return elbow_point or 20

def cluster_embeddings(vectors, num_clusters):
    try:
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10).fit(vectors)
        closest_indices = [np.argmin(np.linalg.norm(vectors - center, axis=1)) for center in kmeans.cluster_centers_]
        return sorted(closest_indices)
    except ValueError as e:
        logging.error(f"Error during clustering embeddings: {e}")
        raise

def generate_chunk_summaries(docs, selected_indices, openai_api_key, custom_prompt, max_workers=10):
    llm3_turbo = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, max_tokens=4096, model='gpt-3.5-turbo-16k')
    map_prompt_template = PromptTemplate(template=f"```{{text}}```\n{custom_prompt}", input_variables=["text"])
    summary_list = []

    def process_chunk(doc):
        return load_summarize_chain(llm=llm3_turbo, chain_type="stuff", prompt=map_prompt_template).run([doc])

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {executor.submit(process_chunk, docs[i]): i for i in selected_indices}
        for future in as_completed(future_to_doc):
            index = future_to_doc[future]
            try:
                chunk_summary = future.result()
                summary_list.append(chunk_summary + "\n" if index < len(selected_indices) - 1 else chunk_summary)
            except Exception as e:
                logging.error(f"Error summarizing document chunk at index {index}: {e}")

    return "".join(summary_list)

def generate_summary(text, openai_api_key, custom_prompt):
    docs, vectors = split_and_embed_text(text, openai_api_key)
    num_chunks = len(docs)
    print(f"Number of chunks: {num_chunks}")  # Debugging

    num_clusters = min(num_chunks, 20)  # Adjust '20' as needed
    print(f"Number of clusters: {num_clusters}")  # Debugging

    if num_chunks > 1:
        selected_indices = cluster_embeddings(vectors, num_clusters)
        print(f"Selected indices for summarization: {selected_indices}")  # Debugging
        final_summary = generate_chunk_summaries(docs, selected_indices, openai_api_key, custom_prompt)
    else:
        final_summary = text if num_chunks == 1 else "Insufficient text for summarization."

    print(f"Final summary: {final_summary[:500]}")  # Debugging: print first 500 characters
    return final_summary
