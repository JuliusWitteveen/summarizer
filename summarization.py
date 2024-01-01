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
    """
    Splits the text into manageable chunks and generates embeddings for each chunk.

    Args:
        text (str): The text to be split and embedded.
        openai_api_key (str): The API key for OpenAI services.

    Returns:
        tuple: A tuple containing the list of document chunks and their corresponding embeddings.
    """
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
    """
    Determines the optimal number of clusters for KMeans clustering based on the elbow method.

    Args:
        vectors (list): The list of embeddings.
        max_clusters (int): The maximum number of clusters to consider.

    Returns:
        int: The optimal number of clusters.
    """
    num_samples = len(vectors)
    if num_samples == 0:
        raise ValueError("No data points available for clustering.")
    
    max_clusters = min(num_samples, max_clusters)
    sse = []
    for k in range(1, max_clusters + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(vectors)
        sse.append(kmeans.inertia_)
    
    elbow_point = KneeLocator(range(1, len(sse) + 1), sse, curve='convex', direction='decreasing').elbow
    return elbow_point or 1

def cluster_embeddings(vectors, num_clusters):
    """
    Clusters the embeddings and identifies the closest document chunk to each cluster center.

    Args:
        vectors (list): The list of embeddings.
        num_clusters (int): The number of clusters to form.

    Returns:
        list: A list of indices representing the closest document chunk to each cluster center.
    """
    try:
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10).fit(vectors)
        closest_indices = [np.argmin(np.linalg.norm(vectors - center, axis=1)) for center in kmeans.cluster_centers_]
        return sorted(closest_indices)
    except ValueError as e:
        logging.error(f"Error during clustering embeddings: {e}")
        raise

def process_chunk(doc, llm3_turbo, map_prompt_template):
    """
    Summarizes a single document chunk using a language model.

    Args:
        doc (str): The document chunk to summarize.
        llm3_turbo (ChatOpenAI): The language model for summarization.
        map_prompt_template (PromptTemplate): The template for generating prompts.

    Returns:
        str: The summary of the document chunk.
    """
    try:
        return load_summarize_chain(llm=llm3_turbo, chain_type="stuff", prompt=map_prompt_template).run([doc])
    except Exception as e:
        logging.error(f"Error summarizing document chunk: {e}")
        return ""

def generate_chunk_summaries(docs, selected_indices, openai_api_key, custom_prompt, max_workers=10):
    """
    Generates summaries for selected document chunks in parallel.

    Args:
        docs (list): The list of document chunks.
        selected_indices (list): The indices of chunks to summarize.
        openai_api_key (str): The API key for OpenAI services.
        custom_prompt (str): The custom prompt for summarization.
        max_workers (int): The maximum number of threads to use.

    Returns:
        str: The combined summary of all selected document chunks.
    """
    llm3_turbo = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, max_tokens=4096, model='gpt-3.5-turbo-16k')
    map_prompt_template = PromptTemplate(template=f"```{{text}}```\n{custom_prompt}", input_variables=["text"])
    summary_list = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {executor.submit(process_chunk, docs[i], llm3_turbo, map_prompt_template): i for i in selected_indices}
        for future in as_completed(future_to_doc):
            index = future_to_doc[future]
            try:
                chunk_summary = future.result()
                summary_list.append(chunk_summary + "\n" if index < len(selected_indices) - 1 else chunk_summary)
            except Exception as e:
                logging.error(f"Error summarizing document chunk at index {index}: {e}")

    return "".join(summary_list)

def compile_summaries(summaries):
    """
    Compiles individual summaries into a final summary.

    Args:
        summaries (list): The list of individual summaries.

    Returns:
        str: The final compiled summary.
    """
    final_summary = "\n".join(summaries)
    return final_summary

def generate_summary(text, api_key, custom_prompt, progress_update_callback=None):
    """
    Orchestrates the entire summarization process.

    Args:
        text (str): The text to summarize.
        api_key (str): The API key for OpenAI services.
        custom_prompt (str): The custom prompt for summarization.
        progress_update_callback (function): A callback function for progress updates.

    Returns:
        str: The final summary of the text.
    """
    docs, vectors = split_and_embed_text(text, api_key)
    if progress_update_callback:
        progress_update_callback(40)

    num_clusters = determine_optimal_clusters(vectors)
    if progress_update_callback:
        progress_update_callback(50)

    llm3_turbo = ChatOpenAI(temperature=0, openai_api_key=api_key, max_tokens=4096, model='gpt-3.5-turbo-16k')
    map_prompt_template = PromptTemplate(template=f"```{{text}}```\n{custom_prompt}", input_variables=["text"])

    summaries = []
    for i, doc in enumerate(docs):
        summary = process_chunk(doc, llm3_turbo, map_prompt_template)
        summaries.append(summary)
        if progress_update_callback:
            progress_update_callback(50 + (40 * (i + 1) // len(docs)))

    final_summary = compile_summaries(summaries)
    if progress_update_callback:
        progress_update_callback(90)

    return final_summary
