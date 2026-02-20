import { useEffect, useState } from "react";

export function useFractalOverlay(symbol) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr(null);

    const url = `${API_URL}/api/fractal/v2.1/overlay?symbol=${encodeURIComponent(symbol)}&windowLen=60&topK=10&aftermathDays=30`;

    fetch(url)
      .then(async (r) => {
        if (!r.ok) throw new Error(`overlay ${r.status}`);
        return await r.json();
      })
      .then((json) => {
        if (!alive) return;
        setData(json);
      })
      .catch((e) => {
        if (!alive) return;
        setErr(e?.message ?? "overlay fetch failed");
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [symbol, API_URL]);

  return { data, loading, err };
}
