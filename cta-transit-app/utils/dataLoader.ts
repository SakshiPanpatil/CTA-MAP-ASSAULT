import type { ProcessedData } from '@/types';

export async function loadCTAData(): Promise<ProcessedData> {
  console.log('Loading CTA data from API...');

  let response: Response;

  try {
    response = await fetch('/api/cta-data', {
      cache: 'no-store',
    });
  } catch (error) {
    console.error('Network error while requesting CTA data:', error);
    throw new Error('Unable to reach CTA data endpoint. Check that the development server is running.');
  }

  if (!response.ok) {
    const details = await safeReadText(response);
    throw new Error(
      `Failed to load CTA data (${response.status} ${response.statusText})${details ? ` - ${details}` : ''}`
    );
  }

  const data = (await response.json()) as ProcessedData;

  console.log('CTA data loaded:', {
    stops: data.stops.length,
    routes: Object.keys(data.routes).length,
  });

  return data;
}

async function safeReadText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return '';
  }
}
