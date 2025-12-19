/**
 * Bakery Quotation API Integration Client
 * Handles communication with the FastAPI backend
 */

interface BakeryApiConfig {
  baseUrl: string;
}

// Configuration
const config: BakeryApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'
};

// ===== API Types =====

export interface QuoteRequest {
  customer_name: string;
  job_type: string;
  quantity: number;
  due_date: string; // YYYY-MM-DD format
  company_name?: string;
  notes?: string;
}

export interface QuoteResponse {
  status: 'success' | 'failure' | 'pending';
  quote_id: string;
  file_path: string;
  total: number;
  currency: string;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database: string;
  bom_api: string;
}

export interface ErrorResponse {
  detail: string | Array<{
    type: string;
    loc: string[];
    msg: string;
    input: any;
  }>;
}

// ===== API Client =====

class BakeryApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get available job types
   */
  async getJobTypes(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/quotes/job-types`);
    if (!response.ok) {
      throw new Error(`Failed to fetch job types: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Create a new quotation
   */
  async createQuote(request: QuoteRequest): Promise<QuoteResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/quotes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle validation errors
      if (response.status === 400 || response.status === 422) {
        const errorData = data as ErrorResponse;
        if (Array.isArray(errorData.detail)) {
          const errors = errorData.detail.map(err => err.msg).join(', ');
          throw new Error(`Validation error: ${errors}`);
        }
        throw new Error(`Validation error: ${errorData.detail}`);
      }
      
      // Handle server errors
      if (response.status >= 500) {
        throw new Error(data.detail || 'Server error occurred');
      }

      throw new Error(`Failed to create quote: ${response.statusText}`);
    }

    return data as QuoteResponse;
  }

  /**
   * Download a quote file
   */
  async downloadQuote(filePath: string): Promise<string> {
    // Since the backend saves files locally, we'll return the file path
    // In production, this should fetch from a proper file storage service
    return filePath;
  }
}

// Export singleton instance
export const bakeryApi = new BakeryApiClient(config.baseUrl);

// Export helper functions
export async function getAvailableJobTypes(): Promise<string[]> {
  return bakeryApi.getJobTypes();
}

export async function createQuotation(request: QuoteRequest): Promise<QuoteResponse> {
  return bakeryApi.createQuote(request);
}

export async function checkApiHealth(): Promise<HealthResponse> {
  return bakeryApi.checkHealth();
}
