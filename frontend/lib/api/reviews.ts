import { apiClient } from '@/lib/api-client';
import type {
  ReviewQueueItem,
  ReviewDecisionRequest,
  DecisionResponse,
  ReviewStatusFilter,
} from '@/types/api';

export interface ReviewListParams {
  page?: number;
  page_size?: number;
  status?: ReviewStatusFilter;
}

export const reviewsApi = {
  list: (params: ReviewListParams = {}): Promise<ReviewQueueItem[]> =>
    apiClient.get('/reviews', { params }).then((r) => r.data.items),

  get: (reviewId: string): Promise<ReviewQueueItem> =>
    apiClient.get(`/reviews/${reviewId}`).then((r) => r.data),

  decide: (reviewId: string, payload: ReviewDecisionRequest): Promise<DecisionResponse> =>
    apiClient.post(`/reviews/${reviewId}/decision`, payload).then((r) => r.data),
};
