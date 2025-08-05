import { Component } from '@angular/core';
import { ApiService } from '../../services/api/api.service';

@Component({
  selector: 'app-code',
  standalone: false,
  templateUrl: './code.component.html',
  styleUrl: './code.component.css'
})
export class CodeComponent {
  code: string = '';
  file: File | null = null;
  modelName: string = 'llama3.1:8b';
  temperature: number = 0.7;
  result: any = null;
  error: string | null = null;
  isLoading: boolean = false;

  constructor(private apiService: ApiService) {}

  onFileChange(event: any) {
    this.file = event.target.files[0];
    this.validateFile();
  }

  validateFile() {
    this.error = null;
    if (!this.file) return;

    const allowedExtensions = ['.txt', '.py', '.js', '.java', '.c', '.cpp'];
    const ext = this.file.name.toLowerCase().substring(this.file.name.lastIndexOf('.'));
    if (!allowedExtensions.includes(ext)) {
      this.error = `Unsupported file type: ${this.file.name}. Allowed types: ${allowedExtensions.join(', ')}`;
      console.error(`Unsupported file type: ${this.file.name}`);
      this.file = null;
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        new TextEncoder().encode(text); // Test UTF-8 compatibility
        console.log(`Validated UTF-8 for file: ${this.file!.name}, size: ${this.file!.size} bytes`);
      } catch (err) {
        this.error = `Invalid UTF-8 encoding in file: ${this.file!.name}. Please ensure the file is UTF-8 encoded.`;
        console.error(`File validation failed for ${this.file!.name}: ${err}`);
        this.file = null;
      }
    };
    reader.onerror = () => {
      this.error = `Failed to read file: ${this.file!.name}.`;
      console.error(`File read error for ${this.file!.name}`);
      this.file = null;
    };
    reader.readAsText(this.file);
  }

  sanitizeText(text: string): string {
    try {
      const sanitized = new TextDecoder('utf-8', { fatal: true }).decode(new TextEncoder().encode(text));
      console.log('Sanitized code:', sanitized.substring(0, 50) + (sanitized.length > 50 ? '...' : ''));
      return sanitized;
    } catch (err) {
      console.error(`Text sanitization failed: ${err}`);
      throw new Error('Invalid UTF-8 characters in input');
    }
  }

  submit() {
    this.error = null;
    this.isLoading = true;

    // Validate and sanitize code
    if (this.code) {
      try {
        this.code = this.sanitizeText(this.code);
      } catch (err) {
        this.error = 'Invalid characters in code input. Please use UTF-8 compatible text.';
        console.error(`Code validation failed: ${err}`);
        this.isLoading = false;
        return;
      }
    }

    if (!this.code && !this.file) {
      this.error = 'Please provide either code or a file.';
      console.error('No code or file provided');
      this.isLoading = false;
      return;
    }

    const formData = new FormData();
    if (this.file) {
      formData.append('code_file', this.file);
      console.log(`Appending file to FormData: ${this.file.name}, size: ${this.file.size} bytes`);
    } else {
      formData.append('code', this.code);
    }
    formData.append('model_name', this.modelName);
    formData.append('temperature', this.temperature.toString());

    // Log FormData contents for debugging
    formData.forEach((value, key) => {
      console.log(`FormData entry: ${key}=${typeof value === 'string' ? value.substring(0, 50) + (value.length > 50 ? '...' : '') : value.name || '[File]'}`);
    });

    this.apiService.analyzeCode(formData).subscribe({
      next: (response) => {
        this.result = response;
        this.error = null;
        this.isLoading = false;
        console.log('Code analysis response:', response);
      },
      error: (err) => {
        this.error = err.error?.error || err.error?.code || err.error?.code_file || 'Code analysis failed';
        this.isLoading = false;
        console.error('Code analysis error:', JSON.stringify(err, null, 2));
      }
    });
  }
}