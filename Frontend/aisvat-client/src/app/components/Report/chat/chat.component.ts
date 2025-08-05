import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ChatService } from '../../../services/websocket/chat.service';

@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit, OnDestroy {
  collectionName: string = '';
  message: string = '';
  messages: any[] = [];
  error: string | null = null;

  constructor(private route: ActivatedRoute, private wsService: ChatService) {}

  ngOnInit() {
    this.collectionName = this.route.snapshot.paramMap.get('collectionName') || '';
    this.wsService.connect(this.collectionName).subscribe({
      next: (data) => {
        if (data.error) {
          this.error = data.error;
        } else {
          this.messages.push(data);
        }
      },
      error: (err) => {
        this.error = err;
      }
    });
  }

  sendMessage() {
    if (this.message.trim()) {
      this.wsService.sendMessage({ message: this.message });
      this.message = '';
    }
  }

  ngOnDestroy() {
    this.wsService.disconnect();
  }
}