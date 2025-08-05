import { Injectable } from '@angular/core';
import { AuthService } from '../auth/auth.service';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class ChatService {

  private ws: WebSocket | null = null;
  private messageSubject = new Subject<any>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(private authService: AuthService) {}

  connect(collectionName: string): Observable<any> {
    const token = this.authService.getToken();
    this.ws = new WebSocket(`${environment.wsUrl}/chat/${collectionName}/?token=${token}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      this.messageSubject.next(JSON.parse(event.data));
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.reconnect(collectionName);
    };

    this.ws.onclose = () => {
      this.reconnect(collectionName);
    };

    return this.messageSubject.asObservable();
  }

  sendMessage(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private reconnect(collectionName: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect(collectionName);
      }, 1000 * this.reconnectAttempts);
    } else {
      this.messageSubject.error('Max reconnect attempts reached');
    }
  }
}
