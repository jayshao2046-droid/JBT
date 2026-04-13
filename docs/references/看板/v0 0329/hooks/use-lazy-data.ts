"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseLazyDataOptions<T> {
  fetchFn: () => Promise<T>;
  cacheKey?: string;
  cacheDuration?: number; // in milliseconds
  enabled?: boolean;
}

interface LazyDataState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

// Simple in-memory cache
const dataCache = new Map<string, { data: unknown; timestamp: number }>();

export function useLazyData<T>({
  fetchFn,
  cacheKey,
  cacheDuration = 5 * 60 * 1000, // 5 minutes default
  enabled = true,
}: UseLazyDataOptions<T>): LazyDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    // Check cache first
    if (cacheKey) {
      const cached = dataCache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < cacheDuration) {
        setData(cached.data as T);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      
      if (mountedRef.current) {
        setData(result);
        
        // Update cache
        if (cacheKey) {
          dataCache.set(cacheKey, { data: result, timestamp: Date.now() });
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err : new Error("Unknown error"));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [fetchFn, cacheKey, cacheDuration]);

  useEffect(() => {
    mountedRef.current = true;
    
    if (enabled) {
      fetchData();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [enabled, fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}

// Hook for intersection observer based lazy loading
export function useIntersectionLazy<T>(
  fetchFn: () => Promise<T>,
  options?: IntersectionObserverInit
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element || hasLoaded) return;

    const observer = new IntersectionObserver(
      async (entries) => {
        if (entries[0].isIntersecting && !hasLoaded) {
          setHasLoaded(true);
          setIsLoading(true);
          
          try {
            const result = await fetchFn();
            setData(result);
          } catch (error) {
            console.error("Lazy load error:", error);
          } finally {
            setIsLoading(false);
          }
        }
      },
      { threshold: 0.1, ...options }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [fetchFn, hasLoaded, options]);

  return { elementRef, data, isLoading, hasLoaded };
}

// Utility to prefetch and cache data
export async function prefetchData<T>(
  key: string,
  fetchFn: () => Promise<T>,
  cacheDuration = 5 * 60 * 1000
): Promise<T> {
  const cached = dataCache.get(key);
  if (cached && Date.now() - cached.timestamp < cacheDuration) {
    return cached.data as T;
  }

  const data = await fetchFn();
  dataCache.set(key, { data, timestamp: Date.now() });
  return data;
}

// Clear cache utility
export function clearDataCache(key?: string) {
  if (key) {
    dataCache.delete(key);
  } else {
    dataCache.clear();
  }
}

// Debounced fetch hook
export function useDebouncedFetch<T>(
  fetchFn: (query: string) => Promise<T>,
  delay = 300
) {
  const [query, setQuery] = useState("");
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!query) {
      setData(null);
      return;
    }

    setIsLoading(true);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(async () => {
      try {
        const result = await fetchFn(query);
        setData(result);
      } catch (error) {
        console.error("Fetch error:", error);
      } finally {
        setIsLoading(false);
      }
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [query, fetchFn, delay]);

  return { query, setQuery, data, isLoading };
}
