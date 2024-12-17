import React from 'react';

const NodeControls = ({ 
  node, 
  nodeWidth, 
  nodeHeight, 
  handleAddNode, 
  handleRemoveNode,
  setIsDrawingConnection,
  setConnectionStart,
  setTempConnectionEnd,
  getScoreColor 
}) => {
  return (
    <>
      {/* Add node button */}
      <g
        transform={`translate(${node.x + nodeWidth/2 + 10}, ${node.y})`}
        onClick={(e) => {
          e.stopPropagation();
          handleAddNode(node);
        }}
        className="cursor-pointer"
      >
        <circle r="12" className="fill-white" stroke={getScoreColor(node.fitness)} />
        <text textAnchor="middle" dominantBaseline="middle" className="text-gray-500 text-lg" fontSize="20">+</text>
      </g>

      {/* Remove node button */}
      <g
        transform={`translate(${node.x - nodeWidth/4}, ${node.y + nodeHeight/2 + 10})`}
        onClick={(e) => {
          e.stopPropagation();
          handleRemoveNode(node.id);
        }}
        className="cursor-pointer"
      >
        <circle r="12" className="fill-white stroke-red-500" />
        <text textAnchor="middle" dominantBaseline="middle" className="fill-red-500 text-lg" fontSize="20">×</text>
      </g>

      {/* Connection button */}
      <g
        transform={`translate(${node.x}, ${node.y + nodeHeight/2 + 10})`}
        onMouseDown={(e) => {
          e.stopPropagation();
          setIsDrawingConnection(true);
          setConnectionStart(node);
          setTempConnectionEnd({ x: node.x, y: node.y });
        }}
        className="cursor-crosshair"
      >
        <circle r="12" className="fill-white stroke-blue-500" />
        <text textAnchor="middle" dominantBaseline="middle" className="fill-blue-500 text-lg" fontSize="20">→</text>
      </g>
    </>
  );
};

export default NodeControls;
