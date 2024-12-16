from pathlib import Path
from fastapi import HTTPException
import json
import os

class GraphStateManager:
    def __init__(self):
        
        self._tmp_folder_ = Path(__file__).parent / "tmp"
        self._tmp_folder_.mkdir(exist_ok=True)
        self._storage_dir = self._tmp_folder_ / "graph_state"
        self._storage_dir.mkdir(exist_ok=True)
        self._state_file = self._storage_dir / "graph_state.json"
        print(f"[Graph] Using state file: {self._state_file}")
        
        self._state = self._load_state() or self._get_initial_state()
        self._websocket_connections = set()
        print("[Graph] GraphStateManager initialized")
    
    def _state_save_path(self):
        save_folder = Path(__file__).parent / 'tmp' / 'graph_state'
        os.makedirs(save_folder, exist_ok=True)
        return save_folder / "graph_state.json"

    def _get_initial_state(self):
        return {
            "nodes": [
                {
                    "id": 1,
                    "x": 300,
                    "y": 300,
                    "name": "Input Node",
                    "target": "input",
                    "input": [],
                    "output": ["data"],
                    "code": "data = 42",
                    "fitness": 0.8,
                    "reasoning": "Initial data input",
                    "inputTypes": [],
                    "outputTypes": ["int"]
                },
                {
                    "id": 2,
                    "x": 550,
                    "y": 300,
                    "name": "Processing Node",
                    "target": "process",
                    "input": ["data"],
                    "output": ["result"],
                    "code": "result = data * 2",
                    "fitness": 0.7,
                    "reasoning": "Double the input value",
                    "inputTypes": ["int"],
                    "outputTypes": ["int"]
                }
            ],
            "connections": [
                {
                    "source": 1,
                    "target": 2
                }
            ]
        }

    def _load_state(self):
        """Load state from file if it exists"""
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, 'r') as f:
                    saved_state = json.load(f)
                print(f"[Graph] Loaded saved state from {self._state_file}")
                return saved_state
            return None
        except Exception as e:
            print(f"[Graph] Error loading state: {str(e)}")
            return None

    def _save_state(self):
        """Save current state to file"""
        try:
           
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._state_file, 'w') as f:
                json.dump(self._state, f, indent=2)
            print(f"[Graph] State saved to {self._state_file}")
        except Exception as e:
            print(f"[Graph] Error saving state: {str(e)}")

    async def broadcast_state(self):
        """Broadcast current state to all connected websockets"""
        message = {
            "type": "graph_update",
            "nodes": self._state["nodes"],
            "connections": self._state["connections"],
        }
        print(f"[Graph] Broadcasting state: {message}")
        for websocket in self._websocket_connections:
            try:
                await websocket.send_json(message)
                print("[Graph] State sent to a connection")
            except Exception as e:
                print(f"[Graph] Error broadcasting state: {str(e)}")
                continue

    def update_state(self, data):
        """Update state with new data"""
        print(f"[Graph] Updating state with: {data}")
        if "nodes" in data:
            self._state["nodes"] = data["nodes"]
        if "connections" in data:
            self._state["connections"] = data["connections"]
        self._save_state()  
        return self._state

    def get_state(self):
        """Get current state"""
        return self._state.copy()

    def add_node(self, node_data: dict):
        """Add a new node"""
        print(f"[Graph] Adding node: {node_data}")
        if any(node["id"] == node_data["id"] for node in self._state["nodes"]):
            raise HTTPException(
                status_code=400, 
                detail=f"Node with id {node_data['id']} already exists"
            )
        self._state["nodes"].append(node_data)
        return self._state

    def update_node(self, node_id: int, node_data: dict):
        """Update existing node"""
        print(f"[Graph] Updating node {node_id} with: {node_data}")
        updated = False
        for i, node in enumerate(self._state["nodes"]):
            if node["id"] == node_id:
                self._state["nodes"][i] = {**node, **node_data}
                updated = True
                break
        if not updated:
            raise HTTPException(
                status_code=404,
                detail=f"Node with id {node_id} not found"
            )
        return self._state

    def remove_node(self, node_id: int):
        """Remove node and its connections"""
        print(f"[Graph] Removing node: {node_id}")
        self._state["nodes"] = [
            node for node in self._state["nodes"] 
            if node["id"] != node_id
        ]
        self._state["connections"] = [
            conn for conn in self._state["connections"]
            if conn["source"] != node_id and conn["target"] != node_id
        ]
        return self._state

    def add_edge(self, edge_data: dict):
        """Add new edge"""
        print(f"[Graph] Adding edge: {edge_data}")
        if not any(node["id"] == edge_data["source"] for node in self._state["nodes"]):
            raise HTTPException(
                status_code=400,
                detail=f"Source node {edge_data['source']} does not exist"
            )
        if not any(node["id"] == edge_data["target"] for node in self._state["nodes"]):
            raise HTTPException(
                status_code=400,
                detail=f"Target node {edge_data['target']} does not exist"
            )
        if any(
            conn["source"] == edge_data["source"] and conn["target"] == edge_data["target"]
            for conn in self._state["connections"]
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Edge from {edge_data['source']} to {edge_data['target']} already exists"
            )
        self._state["connections"].append(edge_data)
        return self._state

    def remove_edge(self, source: int, target: int):
        """Remove edge"""
        print(f"[Graph] Removing edge: {source} -> {target}")
        self._state["connections"] = [
            conn for conn in self._state["connections"]
            if not (conn["source"] == source and conn["target"] == target)
        ]
        return self._state