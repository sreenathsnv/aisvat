import { Component } from '@angular/core';
import { ApiService } from '../../services/api/api.service';
import {News} from '../../models/news.model'
@Component({
  selector: 'app-news',
  standalone: false,
  templateUrl: './news.component.html',
  styleUrl: './news.component.css'
})
export class NewsComponent {
  news: { [source: string]: News[] } = {};
  error: string | null = null;
  isLoading: boolean = false;
  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadNews();
  }

  private loadNews() {
    this.isLoading = true;
    this.error = null;
    
    this.apiService.getNews().subscribe({
      next: (response) => {
        this.news = response.news;
        this.error = null;
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to fetch news';
        this.news = {};
        this.isLoading = false;
      }
    });
  }

 
  retryLoadNews() {
    this.loadNews();
  }
}
