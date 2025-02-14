import asyncio
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv
import reflex as rx
from ragflow_sdk import RAGFlow

load_dotenv()

# Retrieve configuration from environment variables for RAGFlow.
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL")
AGENT_NAME = os.getenv("AGENT_NAME") or os.getenv("RAGFLOW_AGENT_NAME")

if not RAGFLOW_API_KEY:
    raise Exception("Please set RAGFLOW_API_KEY environment variable.")

# Initialize the RAGFlow object.
rag_object = RAGFlow(api_key=RAGFLOW_API_KEY, base_url=RAGFLOW_BASE_URL)
assistant_list = rag_object.list_chats(name=AGENT_NAME)
if not assistant_list:
    raise Exception(f"No chat agent found with name '{AGENT_NAME}'")
assistant = assistant_list[0]


def remove_duplicate_trailing(text: str, min_length: int = 5) -> str:
    """
    Look for a duplicate trailing substring.
    For each possible substring length (from half the text length down to min_length),
    if the text ends with two identical substrings, remove one occurrence.
    """
    n = len(text)
    if n < 2 * min_length:
        return text

    for l in range(n // 2, min_length - 1, -1):
        # Check if the last 2*l characters consist of two identical parts.
        if text[-2 * l:-l] == text[-l:]:
            return text[:-l]
    return text

def clean_response(text: str) -> str:
    """
    Clean the response text by removing internal markers (e.g., '##2$$', '##0$$')
    and duplicate trailing text fragments.
    """
    # Remove markers like ##2$$, ##0$$ (pattern: ##<number>$$)
    cleaned = re.sub(r"##\d+\$\$", "", text)
    # Remove duplicate trailing text if any.
    cleaned = remove_duplicate_trailing(cleaned, min_length=5)
    return cleaned

class QA(rx.Base):
    """A question and answer pair."""
    question: str
    answer: str
    sources: list[str] = []       # Field for storing source links separately.
    show_sources: bool = False    # Controls the dropdown visibility.
    hide_answer: bool = False     # Temporary flag to hide the answer while cleaning.

class State(rx.State):
    """The app state for a single user session."""
    chats: dict[str, list[QA]] = {}
    current_chat: str = ""
    question: str = ""
    processing: bool = False
    new_chat_name: str = ""
    show_sources: bool = False   # Global flag (not used for per-message dropdown now)
    _rag_session: Any = None     # Ephemeral session variable

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the default chat with an opener message.
        self.chats = {"Default": []}
        self.current_chat = "Default"
        # Create an opener message without any sources.
        opener = QA(
            question="",
            answer="Hi, I'm your ACRES Assistant. Ask me any question about the Agri-Climate Rural Environment Scheme.",
            sources=[], # No sources for the opener.
            show_sources=False,  # Do not show a sources dropdown.
            hide_answer=False,
        )
        self.chats["Default"].append(opener)
        # Create a new RAGFlow session for this user.
        self._rag_session = assistant.create_session()

    def create_chat(self):
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = {"Default": []}
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        self.current_chat = chat_name

    @rx.var(cache=False)
    def chat_titles(self) -> list[str]:
        return list(self.chats.keys())

    async def process_question(self, form_data: Dict[str, Any]):
        # Reset global show_sources when a new question is processed.
        self.show_sources = False
        question = form_data["question"]
        if question == "":
            return

        # Process the question using the user-specific RAGFlow session.
        async for _ in self.ragflow_process_question(question):
            yield

    async def ragflow_process_question(self, question: str):
        """
        Process the user's question using the RAGFlow chat assistant.
        Streams responses from the RAGFlow session and updates the chat history.
        """
        # Append the new question with an empty answer and hide its sources and answer initially.
        qa = QA(question=question, answer="", sources=[], show_sources=False, hide_answer=False)
        self.chats[self.current_chat].append(qa)

        # Set the processing flag.
        self.processing = True
        yield

        accumulated_answer = ""
        source_links = set()  # Use a set to avoid duplicate links
        try:
            # Stream the response from the RAGFlow session.
            for message in self._rag_session.ask(question, stream=True):
                if hasattr(message, "content") and message.content:
                    # Get the newly received text chunk.
                    new_part = message.content[len(accumulated_answer):]
                    accumulated_answer = message.content
                    # Clean markers from this chunk.
                    filtered_part = re.sub(r"##\d+\$\$", "", new_part)
                    self.chats[self.current_chat][-1].answer += filtered_part

                    # Process any references.
                    if hasattr(message, "reference") and message.reference:
                        for chunk in message.reference:
                            document_id = None
                            document_name = None
                            if isinstance(chunk, dict):
                                document_id = chunk.get("document_id")
                                document_name = chunk.get("document_name")
                            else:
                                document_id = getattr(chunk, "document_id", None)
                                document_name = getattr(chunk, "document_name", None)
                            if document_id:
                                ext = ""
                                if document_name and "." in document_name:
                                    ext = document_name.split(".")[-1]
                                link = f"http://hcux402.teagasc.net//document/{document_id}?ext={ext}&prefix=document"
                                source_links.add(link)
                    # Update state so the UI reflects the new answer.
                    self.chats = self.chats
                    yield
        except Exception as e:
            self.chats[self.current_chat][-1].answer += f"\nError: {e}"
            self.chats = self.chats

        # After streaming is complete, hide the answer briefly.
        self.chats[self.current_chat][-1].hide_answer = True
        self.chats = self.chats

        # Clean the entire final answer.
        final_answer = clean_response(self.chats[self.current_chat][-1].answer)
        # Wait a short moment before updating so the duplicate isn't visible.
        await asyncio.sleep(0.1)
        self.chats[self.current_chat][-1].answer = final_answer
        self.chats[self.current_chat][-1].hide_answer = False
        self.chats = self.chats

        # Store the sources.
        if source_links:
            self.chats[self.current_chat][-1].sources = list(source_links)
            self.chats = self.chats

        self.processing = False

        # Wait 1 second before showing sources for this new message.
        await asyncio.sleep(1)
        self.chats[self.current_chat][-1].show_sources = True
        self.chats = self.chats
