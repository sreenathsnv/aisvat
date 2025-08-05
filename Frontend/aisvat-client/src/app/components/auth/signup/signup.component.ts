import { Component } from '@angular/core';
import { AuthService } from '../../../services/auth/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-signup',
  standalone: false,
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.css'
})
export class SignupComponent {

  email: string = '';
  full_name: string = '';
  password: string = '';
  rePassword: string = '';
  error: string | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  register() {
    if (this.password !== this.rePassword) {
      this.error = 'Passwords do not match';
      return;
    }
    this.authService.register(this.email, this.full_name, this.password, this.rePassword).subscribe({
      next: () => {
        this.router.navigate(['/login']);
      },
      error: (err) => {
        if (err.error) {
          // If it's a string message directly
          if (typeof err.error === 'string') {
            this.error = err.error;
          }
          // If it's a key-value object, pick the first error message
          else if (typeof err.error === 'object') {
            const firstKey = Object.keys(err.error)[0];
            this.error = err.error[firstKey];
          }
          // Fallback if no known format
          else {
            this.error = 'An unknown error occurred.';
          }
        } else {
          this.error = 'Registration failed. Please try again.';
        }
      }
    });
  }
}
