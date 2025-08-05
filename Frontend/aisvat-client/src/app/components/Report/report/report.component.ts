import { Component } from '@angular/core';
import { ApiService } from '../../../services/api/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-report',
  standalone: false,
  templateUrl: './report.component.html',
  styleUrl: './report.component.css'
})
export class ReportComponent {
  files: File[] = [];
  message: string = '';
  chunkSize: number = 600;
  chunkOverlap: number = 40;
  llmTemperature: number = 0.7;
  maxTokens: number = 1024;
  topK: number = 3;
  modelName: string = 'llama3.1:8b';
  result: any = null;
  error: string | null = null;
  isLoading: boolean = false;
  showAdvancedOptions: boolean = false;
  availableModels: string[] = ['llama3.1:8b'];
  constructor(private apiService: ApiService, private router: Router) {}



  onFileChange(event: any) {
    const fileList: FileList = event.target.files;
    this.files = Array.from(fileList);
    this.validateFiles();
  }

  toggleAdvancedOptions() {
    this.showAdvancedOptions = !this.showAdvancedOptions;
  }

  async validateFiles() {
    const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.py', '.js', '.java', '.c', '.cpp'];
    this.error = null;
    const validFiles: File[] = [];

    for (const file of this.files) {
      const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (!allowedExtensions.includes(ext)) {
        this.error = `Unsupported file type: ${file.name}. Allowed types: ${allowedExtensions.join(', ')}`;
        console.error(`Unsupported file type: ${file.name}`);
        continue;
      }

      if (['.txt', '.py', '.js', '.java', '.c', '.cpp'].includes(ext)) {
        const isValid = await this.validateTextFile(file);
        if (isValid) {
          validFiles.push(file);
        }
      } else {
        validFiles.push(file); // Non-text files are validated by backend
      }
    }

    this.files = validFiles;
    if (this.files.length === 0 && this.error) {
      console.error('All files were invalid; none will be sent.');
    }
  }

  private validateTextFile(file: File): Promise<boolean> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          new TextEncoder().encode(text); // Test UTF-8 compatibility
          console.log(`Validated UTF-8 for file: ${file.name}, size: ${file.size} bytes`);
          resolve(true);
        } catch (err) {
          this.error = `Invalid UTF-8 encoding in file: ${file.name}. Please ensure the file is UTF-8 encoded.`;
          console.error(`File validation failed for ${file.name}: ${err}`);
          resolve(false);
        }
      };
      reader.onerror = () => {
        this.error = `Failed to read file: ${file.name}.`;
        console.error(`File read error for ${file.name}`);
        resolve(false);
      };
      reader.readAsText(file);
    });
  }

  sanitizeText(text: string): string {
    try {
      const sanitized = new TextDecoder('utf-8', { fatal: true }).decode(new TextEncoder().encode(text));
      console.log('Sanitized text:', sanitized.substring(0, 50) + (sanitized.length > 50 ? '...' : ''));
      return sanitized;
    } catch (err) {
      console.error(`Text sanitization failed: ${err}`);
      throw new Error('Invalid UTF-8 characters in input');
    }
  }

  submit() {
    this.error = null;
    this.isLoading = true;

    try {
      if (this.message) {
        this.message = this.sanitizeText(this.message);
      }
    } catch (err) {
      this.error = 'Invalid characters in message. Please use UTF-8 compatible text.';
      console.error(`Message validation failed: ${err}`);
      this.isLoading = false;
      return;
    }

    if (!this.files.length && !this.message) {
      this.error = 'Please provide at least one file or a message.';
      console.error('No files or message provided');
      this.isLoading = false;
      return;
    }

    const formData = new FormData();
    this.files.forEach(file => {
      formData.append('files', file);
      console.log(`Appending file to FormData: ${file.name}, size: ${file.size} bytes`);
    });
    if (this.message) formData.append('message', this.message);
    formData.append('chunk_size', this.chunkSize.toString());
    formData.append('chunk_overlap', this.chunkOverlap.toString());
    formData.append('llm_temperature', this.llmTemperature.toString());
    formData.append('max_tokens', this.maxTokens.toString());
    formData.append('top_k', this.topK.toString());
    formData.append('model_name', this.modelName);

    formData.forEach((value, key) => {
      console.log(`FormData entry: ${key}=${typeof value === 'string' ? value.substring(0, 50) + (value.length > 50 ? '...' : '') : value.name || '[File]'}`);
    });

    this.apiService.processFiles(formData).subscribe({
      next: (response) => {
        this.result = response;
        this.error = null;
        this.isLoading = false;
        console.log('Process files response:', response);
      },
      error: (err) => {
        if (err.status === 401) {
          console.warn('Unauthorized request, redirecting to login page');
          this.router.navigate(['/login']);
        } else {
          this.error = err.error?.error || err.error?.files?.[0] || err.error?.message || 'Failed to process files';
          console.error('Process files error:', JSON.stringify(err, null, 2));
        }
        this.isLoading = false;
      }
    });
  }

  navigateToChat(collection: string) {
    this.router.navigate(['/chat', collection]);
  }
}
