import React from 'react';

const Connection = ({ startNode, endNode, calculatePath, nodeWidth, handleRemoveConnection }) => {
  const path = calculatePath(startNode, endNode, nodeWidth);
  
  const midPoint = {
    x: (startNode.x + endNode.x) / 2,
    y: (startNode.y + endNode.y) / 2
  };
  
  return (
    <g>
      <path
        d={path}
        stroke="#94a3b8"
        strokeWidth="2"
        fill="none"
        markerEnd="url(#arrowhead)"
      />
      <circle r="3" fill="#3b82f6">
        <animateMotion
          dur="1.5s"
          repeatCount="indefinite"
          path={path}
        />
      </circle>
      
      {/* Delete connection button */}
      <g
        transform={`translate(${midPoint.x}, ${midPoint.y})`}
        onClick={() => handleRemoveConnection(startNode.id, endNode.id)}
        className="cursor-pointer opacity-0 hover:opacity-100"
      >
        <circle r="12" className="fill-white stroke-red-500" />
        <text 
          textAnchor="middle" 
          dominantBaseline="middle" 
          className="fill-red-500 text-lg"
          fontSize="20"
        >
          ×
        </text>
      </g>
    </g>
  );
};

export default Connection;