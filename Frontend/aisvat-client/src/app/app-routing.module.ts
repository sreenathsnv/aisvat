import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './components/auth/login/login.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { ActivateComponent } from './components/auth/activate/activate.component';
import { ReportComponent } from './components/Report/report/report.component';
import { authGuard } from './guards/auth.guard';
import { CodeComponent } from './components/code/code.component';
import { NewsComponent } from './components/news/news.component';
import { ChatComponent } from './components/Report/chat/chat.component';
import { ResultComponent } from './components/result/result.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'register', component: SignupComponent },
  { path: 'auth/activate/:uid/:token', component: ActivateComponent },
  { path: 'process', component: ReportComponent, canActivate: [authGuard] },
  { path: 'code-analysis', component: CodeComponent, canActivate: [authGuard] },
  { path: 'news', component: NewsComponent, canActivate: [authGuard] },
  { path: 'chat/:collectionName', component: ChatComponent, canActivate: [authGuard] },
  { path: 'results/:collectionName', component: ResultComponent, canActivate: [authGuard] },
  { path: '', redirectTo: '/login', pathMatch: 'full' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
