import os
import sys
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv(".env")

documents = []
# Create a List of Documents from all of our files in the ./docs folder
files_to_import = os.listdir("docs")
num_files = str(len(files_to_import))
for i, file in enumerate(files_to_import):
    print(f"Importing: {file} {i+1} / {num_files}")
    try:
        if file.endswith(".pdf"):
            pdf_path = "./docs/" + file
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
        elif file.endswith(".docx") or file.endswith(".doc"):
            doc_path = "./docs/" + file
            loader = Docx2txtLoader(doc_path)
            documents.extend(loader.load())
        elif file.endswith(".txt"):
            text_path = "./docs/" + file
            loader = TextLoader(text_path)
            documents.extend(loader.load())
    except Exception as e:
        print("Error importing file: " + file)
        print(e)

# Split the documents into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
documents = text_splitter.split_documents(documents)

# Convert the document chunks to embedding and save them to the vector store
vectordb = Chroma.from_documents(
    documents, embedding=OpenAIEmbeddings(), persist_directory="./data"
)
vectordb.persist()

# create our Q&A chain
pdf_qa = ConversationalRetrievalChain.from_llm(
    ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo"),
    retriever=vectordb.as_retriever(search_kwargs={"k": 6}),
    return_source_documents=True,
    verbose=False,
)

yellow = "\033[0;33m"
green = "\033[0;32m"
white = "\033[0;39m"

chat_history = []
print(
    f"{yellow}---------------------------------------------------------------------------------"
)
print(
    "Welcome to the DocBot. You are now ready to start interacting with your documents"
)
print(
    "---------------------------------------------------------------------------------"
)
while True:
    query = input(f"{green}Prompt: ")
    if query == "exit" or query == "quit" or query == "q" or query == "f":
        print("Exiting")
        sys.exit()
    if query == "":
        continue
    result = pdf_qa({"question": query, "chat_history": chat_history})
    print(f"{white}Answer: " + result["answer"])
    chat_history.append((query, result["answer"]))
