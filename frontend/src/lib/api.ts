const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL 
  ? process.env.NEXT_PUBLIC_API_URL 
  : (typeof window !== 'undefined' ? '/api/v1' : 'http://127.0.0.1:8000/api/v1');

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

export function getDefaultTimeoutForEndpoint(endpoint: string): number {
  if (endpoint.startsWith('/user/settings') || endpoint.startsWith('/settings')) {
    return 15000;
  }
  if (endpoint.includes('/research/') || endpoint.includes('research/status')) {
    return 20000;
  }
  if (endpoint.startsWith('/resume/upload') || endpoint.startsWith('/resume/pipeline') || endpoint.startsWith('/resume/')) {
    return 45000;
  }
  if (endpoint.startsWith('/interview/')) {
    return 45000;
  }
  if (endpoint.startsWith('/auth/')) {
    return 30000;
  }
  return 30000;
}

function resolveRequestSignal(endpoint: string, callerSignal?: AbortSignal | null): AbortSignal | undefined {
  const timeoutMs = getDefaultTimeoutForEndpoint(endpoint);
  const timeoutSignal = typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function'
    ? AbortSignal.timeout(timeoutMs)
    : undefined;

  if (!callerSignal) {
    return timeoutSignal;
  }
  if (!timeoutSignal) {
    return callerSignal;
  }
  if (typeof (AbortSignal as any)?.any === 'function') {
    return (AbortSignal as any).any([callerSignal, timeoutSignal]);
  }
  return callerSignal;
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('careermind_token') : null;

  const headers: Record<string, string> = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const signal = resolveRequestSignal(endpoint, options.signal);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
      signal,
    });

    // A response belongs to the session that sent it. Late failures from a
    // signed-out account must not clear or redirect a newer login.
    if (response.status === 401 && typeof window !== 'undefined' && token
        && localStorage.getItem('careermind_token') === token && !endpoint.startsWith('/auth/')) {
      localStorage.removeItem('careermind_token');
      localStorage.removeItem('careermind_research_job');
      window.location.assign('/login');
    }
    if (response.ok && token && typeof window !== 'undefined'
        && localStorage.getItem('careermind_token') !== token) {
      throw new ApiError('Your session changed. Please retry in your current account.', 409);
    }
    if (response.status === 204) return undefined as T;
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const errorMessage = isJson && Array.isArray(data.detail)
        ? data.detail.map((item: any) => `${item.loc?.slice(1).join('.') || 'Input'}: ${item.msg}`).join('; ')
        : isJson && typeof data.detail === 'string' ? data.detail : 'An unexpected API error occurred';
      throw new ApiError(errorMessage, response.status, data);
    }

    return data as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (options.signal?.aborted) {
      throw new ApiError('Request was cancelled.', 499);
    }
    if (error?.name === 'TimeoutError' || (error?.name === 'AbortError' && !options.signal?.aborted)) {
      throw new ApiError(
        'The request timed out. The server is taking longer than expected to respond. Please try again.',
        408
      );
    }
    throw new ApiError(
      'The server is taking longer than expected or your connection was interrupted. Please try again.',
      503
    );
  }
}
