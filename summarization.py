import file_handler
import language_processing
import summarization
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
selected_file_path = None
progress = None
custom_prompt_area = None

# Set default prompt in English
default_prompt_en = """Summarize the text concisely and directly without prefatory phrases. Focus on presenting its key points and main ideas, ensuring that essential details are accurately conveyed in a straightforward manner."""

# Helper Functions

def get_api_key(file_path=r'C:\\api_key.txt'):
    """
    Retrieves the API key from a specified file. Notifies the user and logs if the file is not found or an error occurs.

    Args:
        file_path (str): The path to the API key file.

    Returns:
        str: The API key, or None if the file is not found or an error occurs.
    """
    logging.info("Retrieving API key.")
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        error_message = f"API key file not found at {file_path}"
        logging.error(error_message)
        messagebox.showerror("API Key Error", error_message)
        return None
    except IOError as e:
        error_message = f"Error reading the API key file: {e}"
        logging.error(error_message)
        messagebox.showerror("API Key Error", error_message)
        return None

def select_file():
    """
    Opens a file dialog for the user to select a document. Logs the file selection process.

    Returns:
        str: The file path of the selected document.
    """
    logging.info("Opening file dialog for document selection.")
    file_path = filedialog.askopenfilename(
        title="Select a Document",
        filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("RTF Files", "*.rtf"), ("Text Files", "*.txt")])
    if file_path:
        logging.info(f"File selected: {file_path}")
    else:
        logging.info("File selection cancelled.")
    return file_path

def get_summary_prompt(file_path, api_key):
    """
    Generates a summary prompt based on the document's language. Defaults to English if language detection fails.

    Args:
        file_path (str): The path of the document.
        api_key (str): The API key for language processing services.

    Returns:
        str: A custom prompt for summarization based on the document's language.
    """
    logging.info(f"Generating summary prompt for file: {file_path}")
    text = file_handler.load_document(file_path)
    if not text:
        logging.warning("No text found in the document.")
        return None

    language = language_processing.detect_language(text)
    if language == "nl":
        return language_processing.translate_prompt(default_prompt_en, language)
    else:
        return default_prompt_en

# Background Summarization Function

def start_summarization_thread(root):
    """
    Starts the summarization process in a separate thread.

    Args:
        root: The root window of the Tkinter application.
    """
    logging.info("Starting summarization in a new thread.")
    summarization_thread = threading.Thread(target=start_summarization, args=(root,))
    summarization_thread.start()

def start_summarization(root):
    """
    Handles the summarization process. Updates the progress bar and provides user feedback.

    Args:
        root: The root window of the Tkinter application.
    """
    global selected_file_path, custom_prompt_area
    api_key = get_api_key()
    if api_key and selected_file_path:
        try:
            logging.info("Starting summarization process.")
            custom_prompt_text = get_summary_prompt(selected_file_path, api_key)
            update_progress_bar(10, root)

            text = file_handler.load_document(selected_file_path)
            update_progress_bar(20, root)

            summary = summarization.generate_summary(
                text, 
                api_key, 
                custom_prompt_text,
                progress_update_callback=lambda value: update_progress_bar(value, root)
            )

            if summary:
                filename_without_ext = os.path.splitext(os.path.basename(selected_file_path))[0]
                root.after(0, lambda: save_summary_file(summary, filename_without_ext))
                update_progress_bar(100, root)
                logging.info("Summarization completed successfully.")
            else:
                logging.warning("Summarization resulted in no content.")
                messagebox.showinfo("Summarization", "The summarization process did not generate any content.")

        except Exception as e:
            error_message = f"Error in summarization process: {e}"
            logging.error(error_message)
            messagebox.showerror("Summarization Error", error_message)
            update_progress_bar(0, root)
    else:
        if not api_key:
            logging.warning("API key is missing or invalid.")
            messagebox.showinfo("API Key Missing", "API key is missing or invalid.")
        if not selected_file_path:
            logging.warning("No file selected for summarization.")
            messagebox.showinfo("File Selection", "No file selected for summarization.")
        update_progress_bar(0, root)

def update_progress_bar(value, root):
    """
    Updates the progress bar in the GUI.

    Args:
        value (int): The progress value to set.
        root: The root window of the Tkinter application.
    """
    logging.debug(f"Updating progress bar to {value}%.")
    def set_progress(value):
        progress['value'] = value
    root.after(0, lambda: set_progress(value))

def save_summary_file(summary, filename_without_ext):
    """
    Opens a save file dialog and saves the summary to a file. Provides user feedback.

    Args:
        summary (str): The summary text to save.
        filename_without_ext (str): The base filename for the summary file.
    """
    logging.info("Opening save file dialog for summary.")
    default_summary_filename = f"{filename_without_ext}_sum"
    file_path = filedialog.asksaveasfilename(
        initialfile=default_summary_filename,
        filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx"), ("PDF Files", "*.pdf")],
        defaultextension=".txt"
    )
    if file_path:
        file_handler.save_summary(summary, file_path)
        messagebox.showinfo("Success", f"Summary saved successfully to {file_path}")
        logging.info(f"Summary saved to {file_path}")
    else:
        logging.warning("Summary saving cancelled by user.")
        messagebox.showerror("Error", "No file path selected for saving the summary.")
