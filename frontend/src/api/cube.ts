import { config } from "../config";
import type { CubeQuery, CubeResponse } from "../types/cube";

export async function loadCubeQuery(
  query: CubeQuery,
  signal?: AbortSignal,
): Promise<CubeResponse> {
  const search = new URLSearchParams({ query: JSON.stringify(query) });
  const response = await fetch(`${config.cubeApiUrl}/load?${search}`, {
    headers: { Accept: "application/json" },
    signal,
  });

  const payload = (await response.json()) as CubeResponse & {
    error?: string;
  };

  if (!response.ok || payload.error) {
    throw new Error(payload.error ?? `Cube API returned ${response.status}`);
  }

  return payload;
}
