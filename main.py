import file_handler
import language_processing
import summarization
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

# Global variables
selected_file_path = None
progress = None
custom_prompt_area = None

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set default prompt in English
default_prompt_en = """Summarize the text concisely and directly without prefatory phrases. Focus on presenting its key points and main ideas, ensuring that essential details are accurately conveyed in a straightforward manner."""

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def get_api_key(file_path=r'C:\api_key.txt'):
    logging.info("Retrieving API key.")
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"API key file not found at {file_path}")
        return None
    except IOError as e:
        logging.error(f"Error reading the API key file: {e}")
        return None

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a Document",
        filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("RTF Files", "*.rtf"), ("Text Files", "*.txt")])
    return file_path

def get_summary_prompt(file_path, api_key):
    text = file_handler.load_document(file_path)
    if not text:
        return None

    language = language_processing.detect_language(text)
    if language == "nl":
        translated_prompt = language_processing.translate_prompt(default_prompt_en, language)
        return translated_prompt
    elif language == "en":
        return default_prompt_en

    return default_prompt_en

# Background Summarization Function
def start_summarization_thread(root):
    summarization_thread = threading.Thread(target=start_summarization, args=(root,))
    summarization_thread.start()

def start_summarization(root):
    global selected_file_path, custom_prompt_area
    api_key = get_api_key()
    if api_key and selected_file_path:
        try:
            # Retrieve the custom prompt text based on the document's language
            custom_prompt_text = get_summary_prompt(selected_file_path, api_key)
            update_progress_bar(10, root)  # Update progress after getting prompt

            # Load the document
            text = file_handler.load_document(selected_file_path)
            update_progress_bar(20, root)  # Update progress after loading document

            # Generate the summary
            summary = summarization.generate_summary(
                text, 
                api_key, 
                custom_prompt_text,
                progress_update_callback=lambda value: update_progress_bar(value, root)
            )

            # Handle the summary (e.g., display, save)
            if summary:
                filename_without_ext = os.path.splitext(os.path.basename(selected_file_path))[0]
                root.after(0, lambda: save_summary_file(summary, filename_without_ext))
                update_progress_bar(100, root)  # Update progress to 100% after completion

        except Exception as e:
            logging.error(f"Error in summarization process: {e}")
            messagebox.showerror("Summarization Error", f"An error occurred during summarization: {e}")
            update_progress_bar(0, root)  # Reset progress bar in case of error
    else:
        messagebox.showinfo("API Key Missing", "API key is missing or invalid.")
        update_progress_bar(0, root)  # Reset progress bar if API key is missing


def update_progress_bar(value, root):
    def set_progress(value):
        progress['value'] = value
    root.after(0, lambda: set_progress(value))

def finalize_process(root):
    update_progress_bar(100, root)

def save_summary_file(summary, filename_without_ext):
    default_summary_filename = f"{filename_without_ext}_sum"
    file_path = filedialog.asksaveasfilename(
        initialfile=default_summary_filename,
        filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx"), ("PDF Files", "*.pdf")],
        defaultextension=".txt"
    )
    if file_path:
        file_handler.save_summary(summary, file_path)
        messagebox.showinfo("Success", f"Summary saved successfully to {file_path}")
    else:
        messagebox.showerror("Error", "No file path selected.")

# -------------------------------------------------------------------
# GUI Code Block
# -------------------------------------------------------------------
def main_gui():
    global selected_file_path, progress, custom_prompt_area

    logging.info("Initializing GUI for the Document Summarizer.")
    root = tk.Tk()
    root.title("Document Summarizer")
    root.state('zoomed')  # Full-screen window

    # Define colors, fonts, and styles
    primary_color = "#2E3F4F"
    secondary_color = "#4F5D75"
    text_color = "#E0FBFC"
    button_color = "#3F88C5"
    larger_font = ('Arial', 12)
    button_font = ('Arial', 10, 'bold')

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('W.TButton', font=button_font, background=button_color, foreground=text_color)
    style.map('W.TButton', background=[('active', secondary_color)], foreground=[('active', text_color)])

    # Configure layout
    root.configure(bg=primary_color)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # Progress bar
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.grid(row=0, column=0, pady=10, padx=10, sticky='ew')

    # Customizable prompt box
    prompt_label = tk.Label(root, text="Customize the summarization prompt:", fg=text_color, bg=primary_color, font=larger_font)
    prompt_label.grid(row=1, column=0, pady=(10, 0), sticky='nw')
    custom_prompt_area = tk.Text(root, height=15, width=80, wrap="word", bd=2, font=larger_font)
    custom_prompt_area.grid(row=2, column=0, pady=10, padx=10, sticky='nsew')

    # Function for file selection
    def file_select():
        global selected_file_path
        selected_file_path = filedialog.askopenfilename(
            title="Select a Document",
            filetypes=[("PDF Files", "*.pdf"), ("Word Documents", "*.docx"), ("RTF Files", "*.rtf"), ("Text Files", "*.txt")])
        
        if selected_file_path:
            api_key = get_api_key()
            if api_key:
                try:
                    text = file_handler.load_document(selected_file_path)
                    if text:
                        language = language_processing.detect_language(text)
                        custom_prompt = default_prompt_en  # Use the default English prompt
                        if language == "nl":
                            dutch_prompt = language_processing.translate_prompt(default_prompt_en, "nl")
                            custom_prompt = dutch_prompt if dutch_prompt else default_prompt_en

                        custom_prompt_area.delete("1.0", tk.END)
                        custom_prompt_area.insert(tk.END, custom_prompt)
                        progress['value'] = 0
                        summarize_button['state'] = 'normal'
                    else:
                        messagebox.showerror("Error", "Failed to load document.")
                        summarize_button['state'] = 'disabled'
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load document: {e}")
                    summarize_button['state'] = 'disabled'
            else:
                messagebox.showinfo("API Key Error", "API key not found. Please check the file path.")
                summarize_button['state'] = 'disabled'
        else:
            summarize_button['state'] = 'disabled'

    # Loading label
    loading_label = tk.Label(root, text="Processing...", fg=text_color, bg=primary_color, font=larger_font)

    # Select file button
    select_button = ttk.Button(root, text="Select Document", command=file_select, style='W.TButton')
    select_button.grid(row=3, column=0, pady=20, padx=10, sticky='ew')

    # Start summarization button
    summarize_button = ttk.Button(root, text="Start Summarization", style='W.TButton')
    summarize_button['command'] = lambda: start_summarization_thread(root)
    summarize_button.grid(row=4, column=0, pady=20, padx=10, sticky='ew')

    root.mainloop()  # This line starts the Tkinter event loop

# -------------------------------------------------------------------
# Script Execution Block
# -------------------------------------------------------------------

if __name__ == '__main__':
    logging.info("Starting the Document Summarizer application.")
    main_gui()
