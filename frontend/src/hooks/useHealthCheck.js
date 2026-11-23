import { useState, useEffect, useCallback } from 'react';
import { healthCheck } from '../services/api';

export const useHealthCheck = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const check = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await healthCheck();
      setData(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return { data, loading, error, refetch: check };
};

export default useHealthCheck;
