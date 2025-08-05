from channels.generic.websocket import AsyncJsonWebsocketConsumer
from chromadb import HttpClient
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from .utils.vulnerability_extraction import get_qa_chain
import json

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.collection_name = self.scope['url_route']['kwargs']['collection_name']
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return

        await self.accept()

        try:
            client = HttpClient(host="chromadb", port=8000)
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self.vectorstore = Chroma(
                client=client,
                collection_name=self.collection_name,
                embedding_function=embeddings,
            )
            self.qa_chain, status = get_qa_chain(self.vectorstore, model_name='llama3.1:8b')
            if not self.qa_chain:
                await self.send_json({"error": status})
                await self.close()
        except Exception as e:
            await self.send_json({"error": f"Failed to initialize QA chain: {str(e)}"})
            await self.close()

    async def receive_json(self, content):
        message = content.get('message')
        if not message:
            await self.send_json({"error": "No message provided"})
            return

        try:
            result = self.qa_chain.invoke({"question": message})
            answer = result.get("answer", "I couldn't generate an answer.")
            sources = result.get("source_documents", [])
            formatted_sources = [
                {
                    "content": source.page_content.strip(),
                    "page": source.metadata.get("page", 0) + 1
                }
                for source in sources[:3]
            ]
            await self.send_json({
                "message": answer,
                "sources": formatted_sources
            })
        except Exception as e:
            await self.send_json({"error": f"Error processing chat: {str(e)}"})

    async def disconnect(self, close_code):
        pass