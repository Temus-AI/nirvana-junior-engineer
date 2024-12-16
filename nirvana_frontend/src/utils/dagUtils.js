export const calculatePath = (startNode, endNode, nodeWidth) => {
  const start = {
    x: startNode.x + nodeWidth/2,
    y: startNode.y
  };
  const end = {
    x: endNode.x - nodeWidth/2,
    y: endNode.y
  };

  const dx = end.x - start.x;
  const dy = end.y - start.y;
  
  const offsetX = Math.min(Math.abs(dx) * 0.7, 150);
  
  const verticalOffset = Math.min(Math.abs(dy) * 0.2, 30);
  
  const controlPoint1 = {
    x: start.x + offsetX,
    y: start.y + (dy > 0 ? verticalOffset : -verticalOffset)
  };
  const controlPoint2 = {
    x: end.x - offsetX,
    y: end.y + (dy > 0 ? -verticalOffset : verticalOffset)
  };

  return `M ${start.x},${start.y} 
          C ${controlPoint1.x},${controlPoint1.y} 
            ${controlPoint2.x},${controlPoint2.y} 
            ${end.x},${end.y}`;
};

export const getScoreColor = (score) => {
  if (score === undefined || score === null || score === 0) return '#94a3b8';
  if (score < 0.5) return '#ef4444';
  if (score < 0.8) return '#f59e0b';
  return '#22c55e';
};
