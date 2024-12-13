from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import json
from datetime import datetime
from tiny_dag.api.chat_manager import ChatManager
from tiny_dag.api.datatypes import NodeData, EdgeData
from tiny_dag.api.graph_manager import GraphStateManager

TEMP_DIR_ = Path(__file__).parent / 'tmp'
TEMP_DIR_.mkdir(exist_ok=True)
TEMP_DIR = TEMP_DIR_ / 'node_request'
TEMP_DIR.mkdir(exist_ok=True)
GRAPH_MANAGER = GraphStateManager()
CHAT_MANAGER = ChatManager()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ready to slot this class into library file
# - Where do I put the util functions?
@app.websocket("/ws")
async def wesocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        GRAPH_MANAGER._websocket_connections.add(websocket)
        while True:
            try:
                data = await websocket.receive_json()
                print(f"[Graph WS] Received data: {data}")

                if data.get("type") == "graph_update":
                    if "nodes" in data and "connections" in data:
                        GRAPH_MANAGER.update_state(data)
                        await GRAPH_MANAGER.broadcast_state()
                        print("[Graph WS] State updated and broadcast")
                    else:
                        print("[Graph WS] Invalid graph update format")
                else:
                    print(f"[Graph WS] Unknown message type: {data.get('type')}")

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[Graph WS] Error: {str(e)}")
                break

    finally:
        GRAPH_MANAGER._websocket_connections.discard(websocket)

# Add these new endpoints
@app.get("/api/graph")
def get_graph():
    """Get current graph state"""
    return GRAPH_MANAGER.get_state()


@app.post("/api/nodes")
async def add_node(node: NodeData):
    """Add a new node and broadcast update"""
    GRAPH_MANAGER.add_node(node.dict())
    await GRAPH_MANAGER.broadcast_state()
    return {"status": "success", "node": node}


@app.put("/api/nodes/{node_id}")
async def update_node(node_id: int, node: NodeData):
    """Update existing node and broadcast"""
    GRAPH_MANAGER.update_node(node_id, node.dict())
    await GRAPH_MANAGER.broadcast_state()
    return {"status": "success", "node": node}


@app.delete("/api/nodes/{node_id}")
async def delete_node(node_id: int):
    """Delete node and broadcast update"""
    GRAPH_MANAGER.remove_node(node_id)
    await GRAPH_MANAGER.broadcast_state()
    return {"status": "success"}


@app.post("/api/edges")
async def add_edge(edge: EdgeData):
    """Add new edge and broadcast update"""
    try:
        print(f"Received edge request: {edge.dict()}")
        # Check if nodes exist
        state = GRAPH_MANAGER.get_state()
        node_ids = [node["id"] for node in state["nodes"]]
        print(f"Existing node IDs: {node_ids}")
        print(f"Looking for source: {edge.source}, target: {edge.target}")

        result = GRAPH_MANAGER.add_edge(edge.dict())
        await GRAPH_MANAGER.broadcast_state()
        return {"status": "success", "edge": edge}
    except Exception as e:
        print(f"Error adding edge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/edges/{source}/{target}")
async def delete_edge(source: int, target: int):
    """Delete edge and broadcast update"""
    GRAPH_MANAGER.remove_edge(source, target)
    await GRAPH_MANAGER.broadcast_state()
    return {"status": "success"}


@app.put("/api/graph")
async def update_graph_state(data: dict):
    """Update entire graph state"""
    try:
        GRAPH_MANAGER.update_state(data)
        await GRAPH_MANAGER.broadcast_state()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-temp-file")
async def save_temp_file(request: dict):
    filename = request["filename"]
    data = request["data"]
    
    file_path = os.path.join(TEMP_DIR, filename)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return {"message": f"File saved: {filename}"}


@app.websocket("/ws/chat")
async def chat_websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        chat_manager = ChatManager()
        chat_manager._websocket_connections.add(websocket)
        await chat_manager.send_history(websocket)

        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "chat_message":
                    message = data.get("message")
                    if message:
                        await chat_manager.process_message(message, websocket)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[Chat] Error: {str(e)}")
                break
    finally:
        chat_manager._websocket_connections.discard(websocket)


def run_server():
    import logging

    import uvicorn

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("chat_websocket")
    uvicorn.run(
        "tiny_dag.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["**/tiny_dag/**/*.py"],
        reload_excludes=["**/node_modules/**"],
        log_level="info",
        workers=1,
    )

if __name__ == "__main__":
    run_server()