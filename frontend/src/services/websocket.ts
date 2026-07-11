import { WebSocketMessage, TickCompletedMessage, AgentActedMessage } from '@/types/api';

type MessageHandler = (message: WebSocketMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;

export class SimulationWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private messageHandlers = new Set<MessageHandler>();
  private statusHandlers = new Set<StatusHandler>();

  constructor(url?: string) {
    const wsBaseUrl =
      process.env.NEXT_PUBLIC_WS_URL ||
      (typeof window !== 'undefined'
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000`
        : 'ws://localhost:8000');
    this.url = url ?? `${wsBaseUrl}/ws`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.notifyStatus('connecting');

    try {
      this.ws = new WebSocket(this.url);
      this.ws.onopen = this.handleOpen;
      this.ws.onmessage = this.handleMessage;
      this.ws.onclose = this.handleClose;
      this.ws.onerror = this.handleError;
    } catch {
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
    this.notifyStatus('disconnected');
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private handleOpen = () => {
    this.reconnectAttempts = 0;
    this.notifyStatus('connected');
  };

  private handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as WebSocketMessage;
      this.messageHandlers.forEach((handler) => handler(data));
    } catch {
      // Ignore malformed messages
    }
  };

  private handleClose = () => {
    this.ws = null;
    this.notifyStatus('disconnected');
    if (this.shouldReconnect) {
      this.scheduleReconnect();
    }
  };

  private handleError = () => {
    if (this.ws) {
      this.ws.close();
    }
  };

  private scheduleReconnect = () => {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) return;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);

    const delay = Math.min(
      BASE_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts),
      MAX_RECONNECT_DELAY,
    );
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  };

  private notifyStatus(status: ConnectionStatus) {
    this.statusHandlers.forEach((handler) => handler(status));
  }
}

export function isTickCompleted(
  msg: WebSocketMessage,
): msg is TickCompletedMessage {
  return msg.type === 'tick_completed';
}

export function isAgentActed(
  msg: WebSocketMessage,
): msg is AgentActedMessage {
  return msg.type === 'agent_acted';
}
