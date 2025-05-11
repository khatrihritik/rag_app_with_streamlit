
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from datetime import datetime
from uuid import uuid4

from app.services.pydantic_models import ChatRequest, ChatResponse
from app.services.logger import logger
from app.utils.db_utils import get_past_conversation_async, add_conversation_async
from app.utils.langchain_utils import generate_chatbot_response, index_documents, generate_chatbot_response_stream
from app.utils.utils import extract_text_from_file
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import json 

router = APIRouter()

@router.post("/upload-knowledge")
async def upload_knwoledge(
    username: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    try:
        extracted_text = ""
        if file:
            logger.info(f"File uploaded: {file.filename}")
            file_content = await file.read()
            file_extension = file.filename.split('.')[-1].lower()
            extracted_text = await extract_text_from_file(file_content, file_extension)
            logger.info(f"File content size: {len(file_content)} bytes")
            logger.info(f"Extracted text from file: {extracted_text}")

            logger.info(f"Indexing documents in QdrantDB")
            await index_documents(username, extracted_text, file.filename, file_extension)

        return {'response': 'Indexed Documents Successfully', 'extracted_text': extracted_text}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing indexing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while indexing documents: {e}")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        start_time = datetime.now()
        logger.info(f"Request started at {start_time}")
        logger.info(f"Received request from {request.username} for question: {request.query}")

        if request.session_id:
            logger.info(f"Fetching past messages")
            past_messages = await get_past_conversation_async(request.session_id)
            logger.info(f"Fetched past messages: {past_messages}")
        else:
            request.session_id = str(uuid4())
            past_messages = []

        logger.info(f"Generating chatbot response")
        response, _, _, _, _, _, refined_query, extracted_documents = await generate_chatbot_response(
            request.query, past_messages, request.no_of_chunks, request.username, request.mode, request.score_threshold)

        logger.info(f"Adding conversation to chat history")
        await add_conversation_async(request.session_id, request.query, response)

        debug_info = {
            "sources": [{"file_name": doc.metadata["file_name"], "context": doc.page_content} for doc in extracted_documents]
        }

        end_time = datetime.now()
        logger.info(f"Request ended at {end_time}")

        return {
            "username": request.username,
            "query": request.query,
            "refine_query": refined_query,
            "response": response,
            "session_id": request.session_id,
            "debug_info": debug_info
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")



@router.post("/chat_stream")
async def chat_stream(request: ChatRequest):
    try:
        # 1. Load or initialize session/history
        if request.session_id:
            past_messages = await get_past_conversation_async(request.session_id)
        else:
            request.session_id = str(uuid4())
            past_messages = []

        # 2. Start the LLM stream
        response_stream, refined_query, extracted_documents = await generate_chatbot_response_stream(
            request.query, past_messages, request.no_of_chunks, request.username, request.mode, request.score_threshold
        )

        collected_chunks: list[str] = []

        # 3. The NDJSON streaming generator with finally
        async def ndjson_generator():
            try:
                # Send session_id first
                yield json.dumps({"session_id": request.session_id}) + "\n"

                # Stream chunks, collecting as we go
                async for chunk in response_stream:
                    collected_chunks.append(chunk)
                    yield json.dumps({"chunk": chunk}) + "\n"

                # Send final debug info
                debug = [
                    {"file_name": doc.metadata["file_name"], "context": doc.page_content}
                    for doc in extracted_documents
                ]
                yield json.dumps({
                    "refined_query": refined_query,
                    "debug_info": {"sources": debug}
                }) + "\n"

            finally:
                # This always runs—whether stream completed, error happened, or client disconnected
                full_response = "".join(collected_chunks)
                try:
                    await add_conversation_async(
                        request.session_id,
                        request.query,
                        full_response
                    )
                except Exception as save_err:
                    logger.error(f"Failed to save conversation: {save_err}")

        # 4. Return the streaming response
        return StreamingResponse(
            ndjson_generator(),
            media_type="application/x-ndjson"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat_stream request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")