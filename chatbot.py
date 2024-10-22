import os
from flask_smorest import Blueprint
from flask import jsonify, request, Response, stream_with_context
from auth import auth
from helpers import format_docs

from langchain_openai import ChatOpenAI
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough



bp = Blueprint("chatbot",
               "items",
               description="Operations on ML model endpoint")

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


llm = ChatOpenAI(model="gpt-4o-mini")
loader = CSVLoader(file_path='data_qna.csv')
data = loader.load()
vectorstore = Chroma.from_documents(documents=data, embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

custom_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
    Anda adalah asisten yang berpengetahuan luas. Berdasarkan konteks berikut, jawablah pertanyaan dengan seakurat mungkin. 
    Hanya jawab pertanyaan yang ada di konteks

    Pertanyaan: {question}
    Konteks: {context}
    
    Jawaban:
    """,
)


@bp.route("/chat", methods=["POST"])
@auth.login_required()
def chat():
    if request.method == "POST":
        input_data = request.get_json()
        message = input_data["message"]
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | custom_prompt
            | llm
            | StrOutputParser()
        )
        
        result = rag_chain.invoke(message)
        
        return jsonify({
            "status": {
                "code": 200,
                "message": "Success get the answers"
            },
            "data": {
                "answer": result
            }
        }), 200
    else:
        return jsonify({
            "status": {
                "code": 405,
                "message": "Invalid request method",
            },
            "data": None,
        }), 405
        
        
@bp.route("/chat_stream", methods=["POST"])
@auth.login_required()
def chat_stream():
    if request.method == "POST":
        input_data = request.get_json()
        message = input_data["message"]
        
        # Build the chain
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | custom_prompt
            | llm
            | StrOutputParser()
        )
        
        # Define the generator function
        def generate():
            # Stream the response
            for chunk in rag_chain.stream(message):
                # 'chunk' is a string containing a part of the output
                yield chunk

        return Response(stream_with_context(generate()), content_type='text/plain')
    else:
        return jsonify({
            "status": {
                "code": 405,
                "message": "Invalid request method",
            },
            "data": None,
        }), 405
