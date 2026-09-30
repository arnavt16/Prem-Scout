import { useEffect, useState } from 'react';

/** Re-fetches whenever any value in `deps` changes. */
export function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // deps is caller-supplied by design (this is a generic fetch hook), so the
  // exhaustive-deps rule can't statically verify it. Disabled for this file
  // in .oxlintrc.json rather than assumed away.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, deps);

  return { data, error, loading };
}
