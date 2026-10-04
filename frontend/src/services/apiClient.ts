import { fetchApi } from '@/lib/api';

export class ApiClient {
  static async get<T>(endpoint: string): Promise<T> {
    return fetchApi<T>(endpoint, { method: 'GET' });
  }

  static async post<T>(endpoint: string, body?: any): Promise<T> {
    return fetchApi<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  static async delete<T>(endpoint: string): Promise<T> {
    return fetchApi<T>(endpoint, { method: 'DELETE' });
  }
}
