import os
from typing import Optional

import PyPDF2
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# NEW: use embeddings from langchain-huggingface
from langchain_huggingface import HuggingFaceEmbeddings

# ------------------- CONFIG -------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ------------------- LOAD ENV & LLM -------------------

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Set it in .env file.")

llm = ChatGroq(model="llama-3.1-8b-instant")
parser = StrOutputParser()

template = """
You are a legal / policy search assistant.
I will provide you a question and documents that may contain the answer.

- Answer the question in maximum 2 lines.
- If the answer is not clearly present in the documents, reply exactly: "dont know Answer".

Question: {question}

Documents:
{document}
"""

prompt = PromptTemplate(
    input_variables=["question", "document"],
    template=template.strip(),
)

chain = prompt | llm | parser

# ------------------- EMBEDDINGS -------------------

_embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ------------------- PUBLIC FUNCTIONS -------------------


def build_vectorstore_from_pdf(
    pdf_path: str, source_name: Optional[str] = None
) -> Chroma:
    """
    Read the provided PDF file, split into chunks,
    and create an in-memory Chroma vector store.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    pdf_reader = PyPDF2.PdfReader(pdf_path)

    all_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text() or ""
        all_text += "\n\n" + text

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_text(all_text)

    src = source_name or os.path.basename(pdf_path)

    documents = [
        Document(
            page_content=chunk,
            metadata={"source": src, "chunk_id": i},
        )
        for i, chunk in enumerate(chunks)
    ]

    db = Chroma.from_documents(
        documents=documents,
        embedding=_embedding,
    )
    return db


def answer_question(db: Chroma, question: str, k: int = 4) -> dict:
    """
    Run similarity search on the given vector DB and answer with the LLM.

    Returns:
    {
      "answer": <str>
    }
    """
    similar_docs = db.similarity_search(question, k=k)
    context = "\n\n".join(d.page_content for d in similar_docs)
    answer = chain.invoke({"question": question, "document": context})

    return {
        "answer": answer,
    }
