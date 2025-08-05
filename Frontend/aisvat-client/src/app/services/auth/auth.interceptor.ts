import { inject } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';
import { HttpErrorResponse, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { catchError, switchMap } from 'rxjs/operators';
import { Observable, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn): Observable<HttpEvent<any>> => {
  const authService = inject(AuthService);
  const token = authService.getToken();
  let authReq = req;

  if (token && !req.url.includes('/auth/')) {
    authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/auth/jwt/refresh/')) {
        return authService.refreshToken().pipe(
          switchMap((response: any) => {
            const newReq = req.clone({
              setHeaders: { Authorization: `Bearer ${response.access}` }
            });
            return next(newReq);
          }),
          catchError((refreshError) => {
            authService.logout();
            return throwError(() => refreshError);
          })
        );
      }
      return throwError(() => error);
    })
  );
};
