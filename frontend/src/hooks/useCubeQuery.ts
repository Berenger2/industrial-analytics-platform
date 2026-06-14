import { useEffect, useMemo, useState } from "react";
import { loadCubeQuery } from "../api/cube";
import type { CubeQuery, CubeRow } from "../types/cube";

type QueryState = {
  data: CubeRow[];
  loading: boolean;
  error: string | null;
};

export function useCubeQuery(query: CubeQuery): QueryState {
  const queryKey = useMemo(() => JSON.stringify(query), [query]);
  const [state, setState] = useState<QueryState>({
    data: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    setState((current) => ({ ...current, loading: true, error: null }));

    void loadCubeQuery(JSON.parse(queryKey) as CubeQuery, controller.signal)
      .then((response) => {
        setState({ data: response.data, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        setState({
          data: [],
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        });
      });

    return () => controller.abort();
  }, [queryKey]);

  return state;
}
