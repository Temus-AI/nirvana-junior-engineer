import React, { useState, useRef, useEffect } from 'react';
import Node from './components/node';
import Connection from './components/connection';
import ChatBox from './components/chatbox';
import { initialNodes, initialConnections } from './data/initialState.js';
import { saveToTempFile } from './utils/fileUtils';
import { chatWebSocket } from './utils/chatWebSocket.js';
import { calculatePath, getScoreColor } from './utils/dagUtils.js';

const SimpleDag = () => {
  const [nodes, setNodes] = useState(initialNodes);
  const [connections, setConnections] = useState(initialConnections);
  
  const [isDragging, setIsDragging] = useState(false);
  const [draggedNode, setDraggedNode] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const [editingNode, setEditingNode] = useState(null);

  
  const nodeWidth = 160;
  const nodeHeight = 40;
  const cornerRadius = 8;


  const [hoveredNode, setHoveredNode] = useState(null);

  const [viewBox, setViewBox] = useState({ x: 0, y: 0, width: 1000, height: 600 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const svgRef = useRef(null);

  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

  // Add useEffect to handle window resizing
  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
      
      // Update viewBox to maintain aspect ratio
      setViewBox(prev => ({
        ...prev,
        width: window.innerWidth,
        height: window.innerHeight
      }));
    };

    window.addEventListener('resize', handleResize);
    

    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleMouseDown = (e, node) => {
    e.stopPropagation();
    setIsDragging(true);
    setDraggedNode(node);
    
    const svgRect = svgRef.current.getBoundingClientRect();
    const scale = svgRect.width / viewBox.width;
    
    setDragOffset({
      x: (e.clientX - svgRect.left) / scale + viewBox.x - node.x,
      y: (e.clientY - svgRect.top) / scale + viewBox.y - node.y
    });
  };

  const handleMouseMove = (e) => {
    if (isDragging && draggedNode) {
      e.preventDefault();
      const svgRect = svgRef.current.getBoundingClientRect();
      const scale = svgRect.width / viewBox.width;
      
      const newX = (e.clientX - svgRect.left) / scale + viewBox.x - dragOffset.x;
      const newY = (e.clientY - svgRect.top) / scale + viewBox.y - dragOffset.y;

      setNodes(nodes.map(node => 
        node.id === draggedNode.id 
          ? { ...node, x: newX, y: newY }
          : node
      ));
    }
  };

  const handleMouseUp = () => {
    if (isDragging && draggedNode) {
      const updatedNode = nodes.find(node => node.id === draggedNode.id);
      if (updatedNode && ws && ws.readyState === WebSocket.OPEN) {
        const stateData = {
          type: "graph_update",
          nodes: nodes,
          connections: connections
        };
        ws.send(JSON.stringify(stateData));
      }
    }
    
    if (isDrawingConnection && hoveredNode) {
      const endNode = nodes.find(n => n.id === hoveredNode);
      if (endNode) {
        handleConnectionComplete(endNode);
      }
    }
    
    setIsDragging(false);
    setDraggedNode(null);
    setIsDrawingConnection(false);
    setConnectionStart(null);
  };

  const handleNodeClick = (e, node) => {
    if (!isDragging && !draggedNode) {
      const svgRect = svgRef.current.getBoundingClientRect();
      const scale = svgRect.width / viewBox.width;
      

      let screenX = (node.x - viewBox.x) * scale + svgRect.left;
      let screenY = (node.y - viewBox.y) * scale + svgRect.top;
      

      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      

      const formWidth = 384;
      const formHeight = Math.min(viewportHeight * 0.8, 600);
      

      if (screenX + formWidth + 20 > viewportWidth) {
        screenX = Math.max(20, screenX - formWidth - 40);
      }
      
      if (screenY + formHeight > viewportHeight) {
        screenY = Math.max(20, viewportHeight - formHeight - 20);
      }
      
      setEditingNode({
        ...node,
        screenX,
        screenY
      });
    }
  };


  const handleAddNode = (sourceNode) => {
    console.log('[Graph] Adding new node from source:', sourceNode);
    
    const maxId = Math.max(...nodes.map(node => node.id), 0);
    const newNodeId = maxId + 1;
    
    const newNode = {
        id: newNodeId,  
        x: sourceNode.x + 300,
        y: sourceNode.y,
        name: `Node ${newNodeId}`,
        target: '',
        input: [],
        output: [],
        code: '',
        reasoning: '',
        inputTypes: [],
        outputTypes: [],
        fitness: 0.0,
        isNewNode: true
    };
    
    const newConnection = {
        source: sourceNode.id,
        target: newNodeId
    };
    

    const updatedNodes = [...nodes, newNode];
    const updatedConnections = [...connections, newConnection];
    setNodes(updatedNodes);
    setConnections(updatedConnections);


    const stateData = {
        type: "graph_update",
        nodes: updatedNodes,
        connections: updatedConnections
    };
    
    console.log('[Graph] Sending new state to backend:', stateData);
    

    saveToTempFile(stateData);
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(stateData));
    }


    setEditingNode({
        ...newNode,
        screenX: newNode.x,
        screenY: newNode.y
    });
  };

  const handleConnectionUpdate = (newConnection) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            connection_update: newConnection
        }));
    }
  };


  const handleSvgMouseDown = (e) => {
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      setIsPanning(true);
      setStartPan({ x: e.clientX, y: e.clientY });
      e.preventDefault();
    }
  };

  const handleSvgMouseMove = (e) => {
    if (isDragging) {
      handleMouseMove(e);
    } else if (isPanning) {
      const dx = (e.clientX - startPan.x) * (viewBox.width / svgRef.current.clientWidth);
      const dy = (e.clientY - startPan.y) * (viewBox.height / svgRef.current.clientHeight);
      
      setViewBox(prev => ({
        ...prev,
        x: prev.x - dx,
        y: prev.y - dy
      }));
      
      setStartPan({ x: e.clientX, y: e.clientY });
    }
    handleConnectionMove(e);
  };

  const handleSvgMouseUp = () => {
    setIsPanning(false);
    handleMouseUp();
    if (isDrawingConnection) {
      setIsDrawingConnection(false);
      setConnectionStart(null);
      setHoveredNode(null);
    }
  };

  // Add zoom handler
  const handleWheel = (e) => {
    // If editing a node, don't prevent default scroll behavior
    if (editingNode) {
      return;
    }
    
    // Only handle zoom when not editing
    const delta = e.deltaY;
    const scaleFactor = delta > 0 ? 1.1 : 0.9;

    // Get mouse position relative to SVG
    const svgRect = svgRef.current.getBoundingClientRect();
    const mouseX = e.clientX - svgRect.left;
    const mouseY = e.clientY - svgRect.top;

    // Convert mouse position to SVG coordinates
    const svgX = (mouseX / svgRect.width) * viewBox.width + viewBox.x;
    const svgY = (mouseY / svgRect.height) * viewBox.height + viewBox.y;

    setViewBox(prev => {
      const newWidth = prev.width * scaleFactor;
      const newHeight = prev.height * scaleFactor;
      
      return {
        x: svgX - (mouseX / svgRect.width) * newWidth,
        y: svgY - (mouseY / svgRect.height) * newHeight,
        width: newWidth,
        height: newHeight
      };
    });
  };

  // Add new state for connection drawing
  const [isDrawingConnection, setIsDrawingConnection] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [tempConnectionEnd, setTempConnectionEnd] = useState({ x: 0, y: 0 });

  // Add new handler for removing nodes
  const handleRemoveNode = (nodeId) => {
    console.log('[Graph] Removing node:', nodeId);
    
    // Update local state
    const updatedNodes = nodes.filter(node => node.id !== nodeId);
    const updatedConnections = connections.filter(conn => 
        conn.source !== nodeId && conn.target !== nodeId
    );
    
    setNodes(updatedNodes);
    setConnections(updatedConnections);

    // Send complete state to backend with type
    const stateData = {
        type: "graph_update",
        nodes: updatedNodes,
        connections: updatedConnections
    };

    // Save to temp file
    saveToTempFile(stateData);
    
    // Send to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(stateData));
        console.log('[Graph] Delete node state sent to backend');
    }
  };

  // Add handleRemoveConnection function
  const handleRemoveConnection = (source, target) => {
    console.log('[Graph] Removing connection:', source, '->', target);
    
    // Update local state
    const updatedConnections = connections.filter(conn => 
        !(conn.source === source && conn.target === target)
    );
    
    setConnections(updatedConnections);

    // Send complete state to backend
    const stateData = {
        type: "graph_update",
        nodes: nodes,
        connections: updatedConnections
    };

    // Save to temp file
    saveToTempFile(stateData);
    
    // Send to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(stateData));
        console.log('[Graph] Delete connection state sent to backend');
    }
  };

  // Add connection drawing handlers
  const handleConnectionMove = (e) => {
    if (isDrawingConnection) {
      const svgRect = svgRef.current.getBoundingClientRect();
      const scale = svgRect.width / viewBox.width;
      const x = (e.clientX - svgRect.left) / scale + viewBox.x;
      const y = (e.clientY - svgRect.top) / scale + viewBox.y;
      setTempConnectionEnd({ x, y });

      // Find node under cursor
      const point = { x, y };
      const nodeUnderCursor = nodes.find(node => 
        node.id !== connectionStart.id && // Ignore source node
        isPointInNodeBounds(point, node)
      );
      
      if (nodeUnderCursor) {
        setHoveredNode(nodeUnderCursor.id);
      } else {
        setHoveredNode(null);
      }
    }
  };

  // Add a small buffer constant for hit detection
  const HIT_DETECTION_BUFFER = 20; // pixels

  // Add helper function to check if point is inside node bounds
  const isPointInNodeBounds = (point, node) => {
    return point.x >= (node.x - nodeWidth/2 - HIT_DETECTION_BUFFER) &&
           point.x <= (node.x + nodeWidth/2 + HIT_DETECTION_BUFFER) &&
           point.y >= (node.y - nodeHeight/2 - HIT_DETECTION_BUFFER) &&
           point.y <= (node.y + nodeHeight/2 + HIT_DETECTION_BUFFER);
  };

  // Update the chat-related state and handlers
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  // Add useEffect for chat WebSocket handling
  useEffect(() => {
    const handleChatMessage = (data) => {
      console.log('[Chat] Message received:', data);
      if (data.type === 'chat_message') {
        setMessages(prev => [...prev, data.message]);
      } else if (data.type === 'chat_history') {
        setMessages(data.messages);
      }
    };

    chatWebSocket.addMessageHandler(handleChatMessage);

    return () => {
      chatWebSocket.removeMessageHandler(handleChatMessage);
    };
  }, []);

  // Update the ChatBox component render
  <ChatBox 
    messages={messages}
    setMessages={setMessages}
    newMessage={newMessage}
    setNewMessage={setNewMessage}
  />

  // Add this function to handle JSON file loading
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const jsonData = JSON.parse(e.target.result);
          // Assuming the JSON has 'nodes' and 'connections' arrays
          if (jsonData.nodes && jsonData.connections) {
            setNodes(jsonData.nodes);
            setConnections(jsonData.connections);
          } else {
            console.error('Invalid JSON format: missing nodes or connections');
          }
        } catch (error) {
          console.error('Error parsing JSON:', error);
        }
      };
      reader.readAsText(file);
    }
  };

  // Add WebSocket state
  const [ws, setWs] = useState(null);

  // Initialize WebSocket connection
  useEffect(() => {
    let websocket;
    try {
        websocket = new WebSocket('ws://localhost:8000/ws');
        
        websocket.onopen = async () => {
            console.log('[Graph] Connected to Python backend');
            
            // Fetch initial state from backend
            try {
                const response = await fetch('http://localhost:8000/api/graph');
                const data = await response.json();
                if (data.nodes && data.nodes.length > 0) {
                    setNodes(data.nodes);
                    setConnections(data.connections || []);
                    console.log('[Graph] Loaded saved state from backend');
                } else {
                    // Only use initialNodes if no saved state exists
                    setNodes(initialNodes);
                    setConnections(initialConnections);
                    console.log('[Graph] No saved state found, using initial state');
                }
            } catch (error) {
                console.error('[Graph] Error fetching initial state:', error);
                // Fallback to initial state if fetch fails
                setNodes(initialNodes);
                setConnections(initialConnections);
            }
        };
        
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "graph_update" && data.nodes && data.connections) {
                    // Only update if we receive non-empty data
                    if (data.nodes.length > 0) {
                        setNodes(data.nodes);
                        setConnections(data.connections);
                        console.log('[Graph] State updated from backend:', data);
                    } else {
                        console.log('[Graph] Received empty state, keeping current state');
                    }
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        websocket.onclose = () => {
            console.log('WebSocket connection closed');
        };
        
        setWs(websocket);
    } catch (error) {
        console.error('Error creating WebSocket connection:', error);
    }
    
    return () => {
        if (websocket) {
            websocket.close();
        }
    };
  }, []);

  const handleEditNode = (node) => {
    // Create a copy of the node without modifying its position
    const nodeToEdit = {
        ...node,
        x: node.x,  // Preserve original position
        y: node.y   // Preserve original position
    };
    setEditingNode(nodeToEdit);
  };

  const handleNodeSave = (nodeId, updatedNode) => {
    console.log('Saving node in SimpleDag:', nodeId, updatedNode); // Debug log

    const updatedNodes = nodes.map(node => 
      node.id === nodeId ? updatedNode : node
    );
    
    setNodes(updatedNodes);
    
    const stateData = {
      type: "graph_update",
      nodes: updatedNodes,
      connections: connections
    };
    
    console.log('Sending state update:', stateData); // Debug log
    
    // Save to temp file
    saveToTempFile(stateData);
    
    // Send to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(stateData));
      console.log('State update sent to WebSocket'); // Debug log
    } else {
      console.warn('WebSocket not ready, update not sent'); // Debug log
    }
  };

  // Update handleSave
  const handleSave = () => {
    if (!editingNode) return;
    
    console.log('[Graph] Saving node:', editingNode);

    // Update nodes state
    const updatedNodes = nodes.map(node => 
      node.id === editingNode.id ? {...editingNode, isNewNode: false} : node
    );
    
    setNodes(updatedNodes);
    
    // Send update to backend
    const stateData = {
      type: "graph_update",
      nodes: updatedNodes,
      connections: connections
    };
    
    console.log('[Graph] Sending updated state to backend:', stateData);
    
    // Save to temp file
    saveToTempFile(stateData);
    
    // Send to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(stateData));
    }
    
    // Close edit form
    setEditingNode(null);
  };

  // Add a function to safely send WebSocket messages
  const sendWebSocketMessage = (message) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(message));
        console.log('[Graph WS] Sent message:', message);
      } catch (error) {
        console.error('[Graph WS] Error sending message:', error);
      }
    } else {
      console.warn('[Graph WS] WebSocket not ready, message not sent');
    }
  };

  // Add this function to handle connection completion
  const handleConnectionComplete = (endNode) => {
    if (connectionStart && endNode && connectionStart.id !== endNode.id) {
      // Check if connection already exists
      const connectionExists = connections.some(
        conn => conn.source === connectionStart.id && conn.target === endNode.id
      );

      if (!connectionExists) {
        const newConnection = {
          source: connectionStart.id,
          target: endNode.id
        };

        // Update local state
        const updatedConnections = [...connections, newConnection];
        setConnections(updatedConnections);

        // Send to backend
        const stateData = {
          type: "graph_update",
          nodes: nodes,
          connections: updatedConnections
        };

        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(stateData));
        }
      }
    }
    
    // Reset connection drawing state
    setIsDrawingConnection(false);
    setConnectionStart(null);
    setTempConnectionEnd({ x: 0, y: 0 });
  };

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <div className="absolute top-4 left-4 z-10">
        <input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          className="hidden"
          id="json-upload"
        />
        <label
          htmlFor="json-upload"
          className="bg-white px-4 py-2 rounded-md shadow-sm border border-gray-300 cursor-pointer hover:bg-gray-50"
        >
          Load JSON
        </label>
      </div>
      
      <svg 
        ref={svgRef}
        className="w-full h-full"
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
        preserveAspectRatio="xMidYMid meet"
        onMouseDown={handleSvgMouseDown}
        onMouseMove={(e) => {
          handleMouseMove(e);
          handleConnectionMove(e);
        }}
        onMouseUp={handleSvgMouseUp}
        onMouseLeave={handleSvgMouseUp}
        onWheel={handleWheel}
        style={{ touchAction: 'none' }}
      >
        <defs>
          <marker
            id="arrowhead"
            viewBox="0 0 10 10"
            refX="5"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="url(#arrowGradient)" />
          </marker>

          <circle id="dataPoint" r="3" fill="url(#dataPointGradient)" />

          <linearGradient id="nodeGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#f8fafc" />
          </linearGradient>

          <linearGradient id="borderGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#cbd5e1" />
            <stop offset="50%" stopColor="#94a3b8" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>

          <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.1"/>
          </filter>

          <linearGradient id="connectionGradient" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#94a3b8" />
            <stop offset="50%" stopColor="#cbd5e1" />
            <stop offset="100%" stopColor="#94a3b8" />
          </linearGradient>

          <linearGradient id="arrowGradient">
            <stop offset="0%" stopColor="#94a3b8" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>

          <radialGradient id="dataPointGradient">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#3b82f6" />
          </radialGradient>

          <filter id="connectionShadow" x="-20%" y="-20%" width="140%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="2" />
            <feOffset dx="1" dy="1" result="offsetblur" />
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.2" />
            </feComponentTransfer>
            <feMerge>
              <feMergeNode />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Modified Edges - now using connections array */}
        {connections.map((connection) => {
          const startNode = nodes.find(node => node.id === connection.source);
          const endNode = nodes.find(node => node.id === connection.target);
          if (startNode && endNode) {
            return (
              <Connection 
                key={`${connection.source}-${connection.target}`}
                startNode={startNode}
                endNode={endNode}
                calculatePath={calculatePath}
                nodeWidth={nodeWidth}
                handleRemoveConnection={handleRemoveConnection}
              />
            );
          }
          return null;
        })}

        {/* Nodes - Modified to include hover detection and plus button */}
        {nodes.map(node => (
          <Node
            key={node.id}
            node={node}
            nodeWidth={nodeWidth}
            nodeHeight={nodeHeight}
            cornerRadius={cornerRadius}
            hoveredNode={hoveredNode}
            isDrawingConnection={isDrawingConnection}
            handleMouseDown={handleMouseDown}
            handleNodeClick={handleNodeClick}
            handleAddNode={handleAddNode}
            handleRemoveNode={handleRemoveNode}
            handleNodeSave={handleNodeSave}
            getScoreColor={getScoreColor}
            setHoveredNode={setHoveredNode}
            setIsDrawingConnection={setIsDrawingConnection}
            setConnectionStart={setConnectionStart}
            setTempConnectionEnd={setTempConnectionEnd}
            isNewNode={node.isNewNode}
          />
        ))}

        {/* Add temporary connection line */}
        {isDrawingConnection && connectionStart && (
          <path
            d={`M ${connectionStart.x},${connectionStart.y} L ${tempConnectionEnd.x},${tempConnectionEnd.y}`}
            stroke={hoveredNode ? "#3b82f6" : "#94a3b8"}
            strokeWidth="2"
            strokeDasharray="5,5"
            fill="none"
          />
        )}
      </svg>

      {/* Chat Box - Show history on hover */}
      <ChatBox 
        messages={messages}
        setMessages={setMessages}
        newMessage={newMessage}
        setNewMessage={setNewMessage}
      />

      {editingNode && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black bg-opacity-30" onClick={() => setEditingNode(null)} />
          
          <div 
            className="absolute bg-white rounded-lg shadow-xl w-96"
            style={{
              left: `${editingNode.screenX + 20}px`,
              top: `${editingNode.screenY}px`,
              maxHeight: '90vh',
            }}
          >
            <div className="flex flex-col h-full">
              {/* Scrollable Content Area */}
              <div 
                className="overflow-y-auto p-6" 
                style={{ 
                  maxHeight: 'calc(90vh - 70px)',
                  overflowY: 'auto',
                  overscrollBehavior: 'contain'
                }}
              >
                <h2 className="text-xl font-bold mb-4">Edit Node</h2>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Name</label>
                    <input
                      type="text"
                      value={editingNode.name}
                      onChange={(e) => setEditingNode({...editingNode, name: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Target</label>
                    <input
                      type="text"
                      value={editingNode.target}
                      onChange={(e) => setEditingNode({...editingNode, target: e.target.value})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Code</label>
                    <textarea
                      value={editingNode.code}
                      onChange={(e) => setEditingNode({...editingNode, code: e.target.value})}
                      rows={4}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Reasoning</label>
                    <textarea
                      value={editingNode.reasoning}
                      onChange={(e) => setEditingNode({...editingNode, reasoning: e.target.value})}
                      rows={4}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Input (comma-separated)</label>
                    <input
                      type="text"
                      value={Array.isArray(editingNode.input) ? editingNode.input.join(', ') : ''}
                      onChange={(e) => setEditingNode({...editingNode, input: e.target.value.split(',').map(s => s.trim())})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Output (comma-separated)</label>
                    <input
                      type="text"
                      value={Array.isArray(editingNode.output) ? editingNode.output.join(', ') : ''}
                      onChange={(e) => setEditingNode({...editingNode, output: e.target.value.split(',').map(s => s.trim())})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Input Types (comma-separated)</label>
                    <input
                      type="text"
                      value={Array.isArray(editingNode.inputTypes) ? editingNode.inputTypes.join(', ') : ''}
                      onChange={(e) => setEditingNode({...editingNode, inputTypes: e.target.value.split(',').map(s => s.trim())})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Output Types (comma-separated)</label>
                    <input
                      type="text"
                      value={Array.isArray(editingNode.outputTypes) ? editingNode.outputTypes.join(', ') : ''}
                      onChange={(e) => setEditingNode({...editingNode, outputTypes: e.target.value.split(',').map(s => s.trim())})}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Fixed Footer with Buttons */}
              <div className="sticky bottom-0 bg-white px-6 py-3 border-t flex justify-end space-x-3 shadow-lg">
                <button
                  onClick={() => setEditingNode(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleDag;