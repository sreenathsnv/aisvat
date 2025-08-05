import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginComponent } from './components/auth/login/login.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { ReportComponent } from './components/Report/report/report.component';
import { ChatComponent } from './components/Report/chat/chat.component';
import { NewsComponent } from './components/news/news.component';
import { CodeComponent } from './components/code/code.component';
import { ActivateComponent } from './components/auth/activate/activate.component';
import { HttpClientModule } from '@angular/common/http';
import { ResultComponent } from './components/result/result.component';
import { NavComponent } from './components/nav/nav.component';

@NgModule({
  declarations: [
    AppComponent,
    ChatComponent,
    LoginComponent,
    SignupComponent,
    ReportComponent,
    ChatComponent,
    NewsComponent,
    CodeComponent,
    ActivateComponent,
    ResultComponent,
    NavComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
