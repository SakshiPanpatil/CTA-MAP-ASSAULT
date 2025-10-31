import path from 'node:path';
import { readFile } from 'node:fs/promises';
import { NextResponse } from 'next/server';
import { parseCSV } from '@/utils/csvParser';
import { processCTAData } from '@/utils/processCTAData';
import type { ProcessedData, Stop, Route, Trip, StopTime, Shape } from '@/types';

export const runtime = 'nodejs';

let cachedData: ProcessedData | null = null;
let pendingLoad: Promise<ProcessedData> | null = null;

export async function GET() {
  try {
    const data = await loadCTADataFromDisk();
    return NextResponse.json(data, {
      headers: {
        'Cache-Control': 'public, max-age=300, stale-while-revalidate=3600',
      },
    });
  } catch (error) {
    console.error('Failed to build CTA data payload:', error);
    cachedData = null;
    pendingLoad = null;
    return NextResponse.json(
      { message: 'Failed to read GTFS files from disk. Verify the dataset in public/data.' },
      { status: 500 },
    );
  }
}

async function loadCTADataFromDisk(): Promise<ProcessedData> {
  if (cachedData) {
    return cachedData;
  }

  if (pendingLoad) {
    return pendingLoad;
  }

  pendingLoad = (async () => {
    const dataDir = path.join(process.cwd(), 'public', 'data');

    const fileContents = await Promise.all([
      readFile(path.join(dataDir, 'stops.txt'), 'utf8'),
      readFile(path.join(dataDir, 'routes.txt'), 'utf8'),
      readFile(path.join(dataDir, 'trips.txt'), 'utf8'),
      readFile(path.join(dataDir, 'stop_times.txt'), 'utf8'),
      readFile(path.join(dataDir, 'shapes.txt'), 'utf8'),
    ]);

    const [stopsText, routesText, tripsText, stopTimesText, shapesText] = fileContents;

    const stops = parseCSV(stopsText) as Stop[];
    const routes = parseCSV(routesText) as Route[];
    const trips = parseCSV(tripsText) as Trip[];
    const stopTimes = parseCSV(stopTimesText) as StopTime[];
    const shapes = parseCSV(shapesText) as Shape[];

    const processed = processCTAData({
      stops,
      routes,
      trips,
      stopTimes,
      shapes,
    });

    cachedData = processed;
    pendingLoad = null;
    return processed;
  })();

  return pendingLoad;
}

