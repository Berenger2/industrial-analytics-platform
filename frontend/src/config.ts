const cubeApiUrl = import.meta.env.VITE_CUBE_API_URL?.trim();

if (!cubeApiUrl) {
  throw new Error("VITE_CUBE_API_URL must be configured");
}

export const config = {
  cubeApiUrl: cubeApiUrl.replace(/\/$/, ""),
} as const;
