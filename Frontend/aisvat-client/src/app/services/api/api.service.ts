import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(private http: HttpClient) {}

  private getHeaders(){
    const token = localStorage.getItem('access_token');

    const httpHeaders = new HttpHeaders()
              .set('Authorization', `Bearer ${token}`);
    

    return httpHeaders;

    }
  processFiles(formData: FormData): Observable<any> {
    return this.http.post(`${environment.apiUrl}/report/`, formData,{
      headers:this.getHeaders()
    });
  }

  analyzeCode(formData: FormData): Observable<any> {
    return this.http.post(`${environment.apiUrl}/code_analysis/`, formData,{
      headers:this.getHeaders()
    });
  }

  getNews(): Observable<any> {
    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders()
          .set('Content-Type', 'application/json')
          .set('Authorization', `Bearer ${token}`);

    return this.http.get(`${environment.apiUrl}/news/`,{
      headers:headers
    });
  }

  getResult(collectionName: string): Observable<any> {

    const token = localStorage.getItem('access_token');
    const headers = new HttpHeaders()
          .set('Content-Type', 'application/json')
          .set('Authorization', `Bearer ${token}`);

    return this.http.get(`${environment.apiUrl}/results/${collectionName}/`,{headers});
  }
}
