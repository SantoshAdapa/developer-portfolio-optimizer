"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * Persist state to sessionStorage so it survives page navigation.
 * Falls back gracefully if sessionStorage is unavailable.
 */
export function usePersistedState<T>(
  key: string,
  initialValue: T
): [T, (val: T | ((prev: T) => T)) => void, () => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const stored = sessionStorage.getItem(key);
      return stored ? (JSON.parse(stored) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // sessionStorage full or unavailable
    }
  }, [key, value]);

  const clear = useCallback(() => {
    setValue(initialValue);
    try {
      sessionStorage.removeItem(key);
    } catch {
      // ignore
    }
  }, [key, initialValue]);

  return [value, setValue, clear];
}
