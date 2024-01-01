# Summarizer

## Overview
The Summarizer is an advanced tool designed to automate the summarization of documents. It efficiently processes PDF, DOCX, RTF, and TXT files using cutting-edge Natural Language Processing (NLP) and machine learning techniques. The project is structured modularly, emphasizing efficiency and responsiveness through multithreaded and asynchronous programming.

## Key Features
- **Multiple File Formats**: Supports PDF, DOCX, RTF, and TXT files.
- **Advanced Text Processing**: Utilizes NLP and machine learning for accurate summarization.
- **Language Detection and Translation**: Automatically detects and translates prompts based on the document's language.
- **Efficient Summarization**: Employs clustering and OpenAI's GPT-3.5 model for generating concise summaries.
- **User-Friendly GUI**: Features a Tkinter-based interface for ease of use.
- **Progress Tracking**: Visual progress indication during the summarization process.

## Dependencies and Compatibility
- Python 3.8 or above.
- Libraries: `fitz` (PyMuPDF), `docx`, `striprtf`, `langchain`, `sklearn`, `numpy`, `langdetect`, `kneed`, `threading`, `tkinter`, `translate`.

## Installation
1. Ensure Python 3.8 or above is installed on your system.
2. Clone the repository: `git clone https://github.com/juliuswitteveen/Summarizer.git`
3. Navigate to the project directory: `cd Summarizer`
4. Install required libraries: `pip install -r requirements.txt`

## Usage
1. Start the application: `python main.py`
2. Use the GUI to select a document for summarization.
3. Optionally, customize the summarization prompt.
4. Initiate the summarization process.
5. Save the generated summary in your preferred format.

## Workflow
- **Initialization**: Sets up global variables, logging, and pre-loads modules.
- **GUI**: Facilitates file selection, custom prompt input, and summarization initiation.
- **Summarization**: Involves document loading, language detection, text preprocessing, clustering, and summary generation.
- **Output**: Displays and allows saving of the final summary.

## Contributing
Contributions to the Summarizer project are welcome. Please read the contributing guidelines before making a pull request.
