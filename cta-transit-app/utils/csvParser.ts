export function parseCSV(text: string): any[] {
  const lines = text.trim().split(/\r?\n/);
  const headerLine = lines[0];
  const headers: string[] = [];
  let current = '';
  let inQuotes = false;

  // Parse headers
  for (let char of headerLine) {
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      headers.push(current.trim().replace(/"/g, ''));
      current = '';
    } else if (char !== '\r') {
      current += char;
    }
  }
  headers.push(current.trim().replace(/"/g, ''));

  const data: any[] = [];

  // Parse data rows
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].replace(/\r$/, '');
    if (!line.trim()) continue;

    const values: string[] = [];
    current = '';
    inQuotes = false;

    for (let char of line) {
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim().replace(/^"|"$/g, ''));
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim().replace(/^"|"$/g, ''));

    const row: any = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    data.push(row);
  }

  return data;
}