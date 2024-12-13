import React from 'react';
import NodeControls from './nodecontrols';

const Node = ({ 
  node, 
  nodeWidth, 
  nodeHeight, 
  cornerRadius, 
  hoveredNode, 
  isDrawingConnection,
  handleMouseDown, 
  handleNodeClick,
  handleAddNode,
  handleRemoveNode,
  getScoreColor,
  setHoveredNode,
  setIsDrawingConnection,
  setConnectionStart,
  setTempConnectionEnd
}) => {
  return (
    <g 
      key={node.id}
      onMouseDown={(e) => handleMouseDown(e, node)}
      onClick={(e) => handleNodeClick(e, node)}
      onMouseEnter={() => !isDrawingConnection && setHoveredNode(node.id)}
      onMouseLeave={() => !isDrawingConnection && setHoveredNode(null)}
    >
      {/* Node rectangle */}
      <rect
        x={node.x - nodeWidth/2}
        y={node.y - nodeHeight}
        width={nodeWidth}
        height={nodeHeight * 2}
        rx={cornerRadius}
        fill="white"
        stroke="url(#borderGradient)"
        strokeWidth="1.5"
        filter="url(#dropShadow)"
      />
      
      {/* Node content */}
      <foreignObject
        x={node.x - nodeWidth/2 + 10}
        y={node.y - nodeHeight + 10}
        width={nodeWidth - 20}
        height={nodeHeight * 2 - 20}
      >
        <div className="flex flex-col h-full justify-center space-y-2">
          <div className="font-bold text-sm text-center">{node.name}</div>
          <div className="text-xs text-gray-600 text-center truncate">{node.target}</div>
        </div>
      </foreignObject>

      {/* Status pill */}
      <rect
        x={node.x + nodeWidth/4 - 1}
        y={node.y - nodeHeight - 15}
        width="32"
        height="22"
        rx="10"
        className="fill-white"
        stroke={getScoreColor(node.fitness)}
        strokeWidth="1.5"
      />
      <text
        x={node.x + nodeWidth/3 + 1}
        y={node.y - nodeHeight - 4}
        className="text-center font-bold"
        fill={getScoreColor(node.fitness)}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={node.fitness === undefined || node.fitness === null || node.fitness === 0 ? "13" : "11"}
      >
        {node.fitness === undefined || node.fitness === null || node.fitness === 0 ? "🚧" : `${Math.round(node.fitness * 100)}%`}
      </text>

      {/* Control buttons */}
      {hoveredNode === node.id && !isDrawingConnection && (
        <NodeControls 
          node={node} 
          nodeWidth={nodeWidth} 
          nodeHeight={nodeHeight * 2}
          handleAddNode={handleAddNode}
          handleRemoveNode={handleRemoveNode}
          setIsDrawingConnection={setIsDrawingConnection}
          setConnectionStart={setConnectionStart}
          setTempConnectionEnd={setTempConnectionEnd}
          getScoreColor={getScoreColor}
        />
      )}
    </g>
  );
};

export default Node;