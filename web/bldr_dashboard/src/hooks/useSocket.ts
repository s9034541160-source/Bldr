import { useState, useEffect, useRef } from 'react';
import { useStore } from '../store';
import { message } from 'antd';
import { useQueryClient } from '@tanstack/react-query';

// Get API base URL from store settings or default to localhost:8000
const getApiBase = () => {
  const store = JSON.parse(localStorage.getItem('store') || '{"settings": {"host": "http://localhost:8000"}}');
  return store.settings?.host || 'http://localhost:8000';
};

// Lightweight event emitter wrapper around native WebSocket to keep on/off API
interface BldrSocket {
  on: (event: string, handler: (data: any) => void) => void;
  off: (event: string, handler: (data: any) => void) => void;
  send: (data: any) => void;
  close: () => void;
}

export const useSocket = () => {
  const [socket, setSocket] = useState<BldrSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const { user } = useStore();
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map());
  const reconnectTimer = useRef<number | null>(null);
  const errorCount = useRef(0); // Track error count to reduce message spam

  useEffect(() => {
    // Don't connect if no user token (keep same behavior)
    if (!user?.token) {
      return;
    }

    const base = getApiBase();
    const proto = base.startsWith('https') ? 'wss' : 'ws';
    const trimmed = base.replace(/\/$/, '');
    // Use the proxy path /ws instead of constructing a full URL
    const wsUrl = '/ws';

    const connect = () => {
      try {
        // Add token to WebSocket URL as query parameter
        const wsUrlWithToken = `${wsUrl}?token=${encodeURIComponent(user.token)}`;
        const ws = new WebSocket(wsUrlWithToken);
        wsRef.current = ws;

        ws.onopen = () => {
          errorCount.current = 0; // Reset error count on successful connection
          setConnected(true);
          // Only show success message if we had previous errors or on first connection
          if (errorCount.current > 0) {
            message.success('WebSocket подключен');
          }
        };

        ws.onclose = () => {
          setConnected(false);
          // Try to reconnect after delay
          if (reconnectTimer.current == null) {
            reconnectTimer.current = window.setTimeout(() => {
              reconnectTimer.current = null;
              connect();
            }, 3000);
          }
        };

        ws.onerror = (err: any) => {
          setConnected(false);
          console.error('WebSocket error:', err);
          errorCount.current++;
          // Only show error message every 5 errors to reduce spam
          if (errorCount.current % 5 === 1) {
            message.warning('WS ошибка, переключаемся на polling');
          }
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            // Normalize events: job_update/task_update/job_completed -> 'task_update'
            let eventName = msg.type || 'message';
            let payload = msg;

            if (msg.type === 'job_update') {
              eventName = 'task_update';
              payload = {
                id: msg.job_id || msg.id,
                progress: msg.data?.progress ?? msg.progress ?? 0,
                status: msg.data?.status ?? msg.status,
                message: msg.data?.message ?? msg.message,
                type: msg.tool_type || msg.type || 'unknown'
              };
            } else if (msg.type === 'job_completed') {
              eventName = 'task_update';
              payload = {
                id: msg.job_id || msg.id,
                progress: 100,
                status: 'completed',
                message: msg.message || 'Задача завершена',
                type: msg.tool_type || 'unknown'
              };
            } else if (msg.type === 'task_update') {
              payload = msg.data || msg;
              if (!payload.id && msg.job_id) payload.id = msg.job_id;
            }

            // Emit to local subscribers
            const set = handlersRef.current.get(eventName);
            if (set) {
              set.forEach(h => {
                try { h(payload); } catch {}
              });
            }

            // Update react-query cache for queue like before
            if (eventName === 'task_update' && payload?.id) {
              queryClient.setQueryData(['queue', 'active'], (old: any[] | undefined) => {
                if (!old) return [payload];
                return old.map(task => task.id === payload.id ? { ...task, ...payload } : task);
              });

              // Also push into completed cache when done
              if (payload.status === 'completed' || payload.progress === 100) {
                queryClient.setQueryData(['queue', 'completed'], (old: any[] | undefined) => {
                  const exists = (old || []).some(t => t.id === payload.id);
                  if (exists) return old;
                  const item = {
                    id: payload.id,
                    type: payload.type || 'unknown',
                    status: 'completed',
                    progress: 100,
                    owner: payload.owner || 'system',
                    started_at: payload.started_at || new Date().toISOString(),
                    eta: null
                  };
                  return [...(old || []), item];
                });
              }
            }
          } catch (e) {
            // ignore invalid JSON
          }
        };
      } catch (e) {
        setConnected(false);
        console.error('WebSocket connection error:', e);
        errorCount.current++;
        // Only show error message every 5 errors to reduce spam
        if (errorCount.current % 5 === 1) {
          message.warning('WS ошибка, переключаемся на polling');
        }
      }
    };

    connect();

    const bldrSocket: BldrSocket = {
      on: (event, handler) => {
        const set = handlersRef.current.get(event) || new Set();
        set.add(handler);
        handlersRef.current.set(event, set);
      },
      off: (event, handler) => {
        const set = handlersRef.current.get(event);
        if (set) {
          set.delete(handler);
          if (set.size === 0) handlersRef.current.delete(event);
        }
      },
      send: (data) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
        }
      },
      close: () => {
        if (wsRef.current) wsRef.current.close();
      }
    };

    setSocket(bldrSocket);

    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (wsRef.current) wsRef.current.close();
      handlersRef.current.clear();
    };
  }, [user?.token, queryClient]);

  return { socket, connected };
};