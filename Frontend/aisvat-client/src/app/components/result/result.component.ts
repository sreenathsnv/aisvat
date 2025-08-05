import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../services/api/api.service';

@Component({
  selector: 'app-result',
  standalone: false,
  templateUrl: './result.component.html',
  styleUrl: './result.component.css'
})
export class ResultComponent implements OnInit {
  collectionName: string = '';
  result: any = null;
  error: string | null = null;
  isLoading:boolean | null = null;
  
  constructor(private route: ActivatedRoute, private apiService: ApiService) {}

  ngOnInit() {
    this.collectionName = this.route.snapshot.paramMap.get('collectionName') || '';
    this.apiService.getResult(this.collectionName).subscribe({
      next: (response) => {
        this.result = response;
        this.error = null;
      },
      error: (err) => {
        this.error = err.error?.error || 'Failed to load result';
        this.result = null;
      }
    });
  }
}