import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../services/auth/auth.service';

@Component({
  selector: 'app-activate',
  standalone: false,
  templateUrl: './activate.component.html',
  styleUrl: './activate.component.css'
})
export class ActivateComponent implements OnInit {
  message: string = 'Activating account...';
  error: string | null = null;

  constructor(private route: ActivatedRoute, private authService: AuthService, private router: Router) {}

  ngOnInit() {
    const uid = this.route.snapshot.paramMap.get('uid');
    const token = this.route.snapshot.paramMap.get('token');
    if (uid && token) {
      this.authService.activate(uid, token).subscribe({
        next: () => {
          this.message = 'Account activated successfully!';
          setTimeout(() => this.router.navigate(['/login']), 2000);
        },
        error: (err) => {
          this.error = err.error?.detail || 'Activation failed';
        }
      });
    } else {
      this.error = 'Invalid activation link';
    }
  }
}