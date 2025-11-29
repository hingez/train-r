import { useState, useEffect, useCallback, useRef } from 'react';
import type { Message, UserMessage, ConfirmationResponse } from '@/types/messages';

interface UseWebSocketReturn {
  messages: Message[];
  sendMessage: (content: string) => void;
  sendConfirmation: (response: ConfirmationResponse) => void;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  error: string | null;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('connecting');
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message: Message = JSON.parse(event.data);
          setMessages((prev) => [...prev, message]);
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionStatus('error');
        setError('Connection error occurred');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect:', err);
      setConnectionStatus('error');
      setError('Failed to establish connection');
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message: UserMessage = {
        type: 'user_message',
        content,
      };
      wsRef.current.send(JSON.stringify(message));
      // Add user message to local state immediately
      setMessages((prev) => [...prev, message]);
    } else {
      console.error('WebSocket is not connected');
      setError('Cannot send message: not connected');
    }
  }, []);

  const sendConfirmation = useCallback((response: ConfirmationResponse) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(response));
      // Remove the confirmation request from messages after response
      setMessages((prev) => prev.filter(m =>
        m.type !== 'confirmation_request' ||
        (m as any).confirmation_id !== response.confirmation_id
      ));
    } else {
      console.error('WebSocket is not connected');
      setError('Cannot send confirmation: not connected');
    }
  }, []);

  return {
    messages,
    sendMessage,
    sendConfirmation,
    connectionStatus,
    error,
  };
}
