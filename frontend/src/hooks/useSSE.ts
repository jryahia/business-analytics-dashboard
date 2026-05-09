import { useEffect, useRef, useCallback } from "react";

type EventHandler = (data: Record<string, unknown>) => void;

export function useSSE(handlers: Record<string, EventHandler>): void {
  const token = localStorage.getItem("token");
  const esRef = useRef<EventSource | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const connect = useCallback(() => {
    if (!token) return;
    const baseUrl = import.meta.env.VITE_API_URL || "";
    const es = new EventSource(`${baseUrl}/api/events`, {
      // EventSource doesn't support custom headers, use query param fallback
    });
    esRef.current = es;

    es.addEventListener("heartbeat", () => {});

    Object.keys(handlersRef.current).forEach((eventType) => {
      es.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as Record<string, unknown>;
          handlersRef.current[eventType]?.(data);
        } catch {}
      });
    });

    es.onerror = () => {
      es.close();
      setTimeout(connect, 5000);
    };
  }, [token]);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
    };
  }, [connect]);
}
