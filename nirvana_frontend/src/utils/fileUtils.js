export const saveToTempFile = async (data, type = 'state') => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `temp_${type}_${timestamp}.json`;
  
  try {
    const response = await fetch('http://localhost:8000/save-temp-file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename,
        data,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to save file');
    }

    console.log(`File saved: ${filename}`);
  } catch (error) {
    console.error('Error saving file:', error);
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  }
}; 