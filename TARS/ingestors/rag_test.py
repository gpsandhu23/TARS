from langchain_community.document_loaders import WebBaseLoader
from dotenv import load_dotenv
import json

load_dotenv()


loader = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/")
docs = loader.load()

loader = WebBaseLoader("https://lilianweng.github.io/posts/2024-02-05-human-data-quality/")
docs.extend(loader.load())

# print("doc source url:", docs[0].metadata["source"])

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


chain = (
    {"doc": lambda x: x.page_content}
    | ChatPromptTemplate.from_template("Can you please produce 10 'question' and 'ideal_answer' pairs for the following document in JSON format:\n\n{doc}")
    | ChatOpenAI(model="gpt-4-turbo-preview",max_retries=0)
    | StrOutputParser()
)

evals = chain.batch(docs, {"max_concurrency": 5})
print("Evals:", evals)

# save evals to a json file
with open("evals.json", "w") as f:
    json.dump(evals, f)


# chain = (
#     {"doc": lambda x: x.page_content}
#     | ChatPromptTemplate.from_template("Summarize the following document:\n\n{doc}")
#     | ChatOpenAI(model="gpt-3.5-turbo",max_retries=0)
#     | StrOutputParser()
# )

# summaries = chain.batch(docs, {"max_concurrency": 5})

# # print("summaries:", summaries)

# from langchain.storage import InMemoryByteStore
# from langchain_openai import OpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
# from langchain.retrievers.multi_vector import MultiVectorRetriever

# # The vectorstore to use to index the child chunks
# vectorstore = Chroma(collection_name="summaries",
#                      embedding_function=OpenAIEmbeddings())

# retriever = vectorstore

# # Setup the parent document urls
# source_url = "source_url"


# doc_url_sources = [doc.metadata["source"] for doc in docs]

# # Docs linked to summaries
# summary_docs = [
#     Document(page_content=s, metadata={source_url: doc_url_sources[i]})
#     for i, s in enumerate(summaries)
# ]

# # print("summary_docs:", summary_docs)

# # Add
# retriever.add_documents(summary_docs)


# query = "Memory in agents"
# # similar_docs = vectorstore.similarity_search(query,k=2)
# # print("Similar docs:", similar_docs)


# similar_docs = retriever.similarity_search(query,k=2)
# print("Similar docs:", similar_docs)

# similar_docs_urls = [doc.metadata["source_url"] for doc in similar_docs]
# print("Similar docs urls:", similar_docs_urls)
