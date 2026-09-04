import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../lib/api/client';
import { ApiClientError } from '../lib/api/errors';

describe('ApiClient', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    globalThis.fetch = mockFetch as unknown as typeof fetch;
  });

  it('should successfully parse JSON on 200 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers(),
      text: async () => JSON.stringify({ data: 'success' }),
    });

    const client = new ApiClient({ fetchImpl: mockFetch });
    const response = await client.get('/test');
    
    expect(response).toEqual({ data: 'success' });
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/test',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('should throw ApiClientError on backend error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      headers: new Headers({ 'X-Request-ID': 'req-123' }),
      text: async () => JSON.stringify({
        success: false,
        error: { code: 'INVALID_INPUT', message: 'Bad request' }
      }),
    });

    const client = new ApiClient({ fetchImpl: mockFetch });
    
    try {
      await client.get('/test');
      expect.fail('Should have thrown an error');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      const apiError = error as ApiClientError;
      expect(apiError.code).toBe('INVALID_INPUT');
      expect(apiError.message).toBe('Bad request');
      expect(apiError.status).toBe(400);
      expect(apiError.requestId).toBe('req-123');
    }
  });

  it('should attach auth token if getToken is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers(),
      text: async () => JSON.stringify({}),
    });

    const client = new ApiClient({
      fetchImpl: mockFetch,
      getToken: () => 'fake-token'
    });
    
    await client.get('/test');
    
    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers.get('Authorization')).toBe('Bearer fake-token');
  });
});
