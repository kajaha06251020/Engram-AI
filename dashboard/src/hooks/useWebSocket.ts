"use client";

import { useEffect, useRef, useCallback } from "react";

type EventHandler = (data: unknown) => void;

export function useWebSocket(handlers: Record<string, EventHandler>) {
  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const retriesRef = useRef(0);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const handler = handlersRef.current[msg.event];
        if (handler) handler(msg.data);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (retriesRef.current < 5) {
        const delay = Math.min(1000 * 2 ** retriesRef.current, 30000);
        retriesRef.current++;
        setTimeout(connect, delay);
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);
}
