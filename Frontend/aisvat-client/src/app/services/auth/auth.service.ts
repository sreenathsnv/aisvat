import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private tokenSubject = new BehaviorSubject<string | null>(localStorage.getItem('access_token'));
  private refreshTokenSubject = new BehaviorSubject<string | null>(localStorage.getItem('refresh_token'));

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/jwt/create/`, { email, password }).pipe(
      tap((response: any) => {
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        this.tokenSubject.next(response.access);
        this.refreshTokenSubject.next(response.refresh);
      })
    );
  }

  register(email: string, full_name: string, password: string, re_password: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/users/`, { email, full_name, password, re_password });
  }

  activate(uid: string, token: string): Observable<any> {
    return this.http.post(`${environment.apiUrl}/auth/users/activation/`, { uid, token });
  }

  refreshToken(): Observable<any> {
    const refresh = this.refreshTokenSubject.value;
    return this.http.post(`${environment.apiUrl}/auth/jwt/refresh/`, { refresh }).pipe(
      tap((response: any) => {
        localStorage.setItem('access_token', response.access);
        this.tokenSubject.next(response.access);
      })
    );
  }

  isAuthenticated(): boolean {
    return !!this.tokenSubject.value;
  }

  getToken(): string | null {
    return this.tokenSubject.value;
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.tokenSubject.next(null);
    this.refreshTokenSubject.next(null);
    this.router.navigate(['/login']);
  }
}
