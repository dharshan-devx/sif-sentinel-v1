'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { reviewsApi } from '@/lib/api/reviews';
import {
  ReviewDecisionBadge
} from '@/components/ui/status-badges';
import { ErrorState, EmptyState, Skeleton } from '@/components/ui/states';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { AxiosError } from 'axios';
import type { ApiErrorBody, ReviewQueueItem, ReviewDecision, ReviewStatusFilter, SIFLevel, BarrierStatus } from '@/types/api';
import { CheckSquare, CheckCircle, XCircle, Edit3, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { useAuth } from '@/components/providers/AuthProvider';

interface DecisionDialogProps {
  review: ReviewQueueItem | null;
  open: boolean;
  onClose: () => void;
}

function DecisionDialog({ review, open, onClose }: DecisionDialogProps) {
  const queryClient = useQueryClient();
  const [decision, setDecision] = useState<ReviewDecision>('APPROVE');
  const [comment, setComment] = useState('');
  
  // Correction fields
  const [correctedSifLevel, setCorrectedSifLevel] = useState<SIFLevel | ''>('');
  const [correctedActivity, setCorrectedActivity] = useState('');
  const [correctedHazard, setCorrectedHazard] = useState('');
  const [correctedBarrier, setCorrectedBarrier] = useState('');
  const [correctedBarrierStatus, setCorrectedBarrierStatus] = useState<BarrierStatus | ''>('');
  const [correctedBarrierFailure, setCorrectedBarrierFailure] = useState('');
  const [correctedLsr, setCorrectedLsr] = useState('');

  useEffect(() => {
    if (review) {
      setDecision(review.decision === 'PENDING' ? 'APPROVE' : review.decision);
      setComment(review.reviewer_comment || '');
      setCorrectedSifLevel(review.corrected_sif_level || '');
      setCorrectedActivity(review.corrected_activity || '');
      setCorrectedHazard(review.corrected_hazard || '');
      setCorrectedBarrier(review.corrected_barrier || '');
      setCorrectedBarrierStatus(review.corrected_barrier_status || '');
      setCorrectedBarrierFailure(review.corrected_barrier_failure || '');
      setCorrectedLsr(review.corrected_life_saving_rule || '');
    }
  }, [review]);

  const mutation = useMutation({
    mutationFn: () =>
      reviewsApi.decide(review!.id, {
        decision,
        reviewer_comment: comment || undefined,
        corrected_sif_level: (decision === 'MODIFY' && correctedSifLevel) ? correctedSifLevel : undefined,
        corrected_activity: (decision === 'MODIFY' && correctedActivity) ? correctedActivity : undefined,
        corrected_hazard: (decision === 'MODIFY' && correctedHazard) ? correctedHazard : undefined,
        corrected_barrier: (decision === 'MODIFY' && correctedBarrier) ? correctedBarrier : undefined,
        corrected_barrier_status: (decision === 'MODIFY' && correctedBarrierStatus) ? correctedBarrierStatus : undefined,
        corrected_barrier_failure: (decision === 'MODIFY' && correctedBarrierFailure) ? correctedBarrierFailure : undefined,
        corrected_life_saving_rule: (decision === 'MODIFY' && correctedLsr) ? correctedLsr : undefined,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] });
      toast.add({ title: 'Decision recorded', description: `${data.decision} — ${data.report_id}`, type: 'success' });
      onClose();
    },
    onError: (error: AxiosError<ApiErrorBody>) => {
      toast.add({ title: 'Decision failed', description: error.response?.data?.error?.message ?? 'Failed', type: 'error' });
    },
  });

  if (!review) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-5xl max-w-5xl h-[90vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 py-4 border-b border-border bg-muted/20 shrink-0">
          <DialogTitle>Review Decision — {review.report_id}</DialogTitle>
          <DialogDescription>Submit your authoritative human review decision on this AI-generated safety analysis.</DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 h-full">
            
            {/* Left Column: Original AI Output */}
            <div className="p-6 border-r border-border/50 bg-background/50 backdrop-blur-sm space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                  <span className="text-xl">🤖</span> AI Analysis Original Output
                </h3>
                
                <div className="p-4 bg-muted/10 border border-border/50 rounded-xl text-sm shadow-sm mb-4">
                  <p className="text-xs text-muted-foreground font-medium mb-2 uppercase tracking-wider">Report Narrative</p>
                  <p className="text-foreground/90 leading-relaxed">{review.report_text}</p>
                </div>

                {review.explanation && (
                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl text-sm shadow-sm mb-6">
                    <p className="text-xs text-blue-400 font-medium mb-2 uppercase tracking-wider">AI Explanation & Reasoning</p>
                    <p className="text-blue-100/90 leading-relaxed">{review.explanation}</p>
                  </div>
                )}
                
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-muted/10 border border-border/50 rounded-xl shadow-sm">
                      <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider mb-1">SIF Level</p>
                      <p className="text-sm font-semibold text-foreground">{review.original_sif_level || 'N/A'}</p>
                    </div>
                    <div className="p-4 bg-muted/10 border border-border/50 rounded-xl shadow-sm">
                      <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider mb-1">Life Saving Rule</p>
                      <p className="text-sm font-medium text-foreground">{review.original_life_saving_rule || 'N/A'}</p>
                    </div>
                  </div>

                  <div className="p-5 bg-muted/10 border border-border/50 rounded-xl shadow-sm space-y-4">
                    <p className="text-xs font-semibold text-foreground border-b border-border/50 pb-2">Precursor Pattern Details</p>
                    <div className="space-y-3">
                      <div>
                        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Activity</p>
                        <p className="text-sm text-foreground/90">{review.original_activity || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Hazard</p>
                        <p className="text-sm text-foreground/90">{review.original_hazard || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Barrier</p>
                        <p className="text-sm text-foreground/90">{review.original_barrier || 'N/A'} <span className="text-xs text-muted-foreground ml-2">({review.original_barrier_status || 'N/A'})</span></p>
                      </div>
                      <div>
                        <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">Barrier Failure</p>
                        <p className="text-sm text-foreground/90">{review.original_barrier_failure || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Review Action */}
            <div className="p-6 bg-background space-y-6">
              <div className="space-y-2">
                <Label htmlFor="review_decision" className="text-base text-foreground font-medium">Your Decision <span className="text-red-500">*</span></Label>
                <Select value={decision} onValueChange={(v) => setDecision(v as ReviewDecision)}>
                  <SelectTrigger id="review_decision" className="h-12 text-base bg-muted/20 border-border/50"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APPROVE">✓ Approve — AI analysis is correct</SelectItem>
                    <SelectItem value="REJECT">✗ Reject — AI analysis is incorrect</SelectItem>
                    <SelectItem value="MODIFY">✎ Modify — Partial correction needed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {decision === 'MODIFY' && (
                <div className="space-y-4 p-5 border-2 border-orange-500/20 rounded-xl bg-orange-500/10">
                  <p className="text-sm font-semibold text-orange-400 flex items-center gap-2">
                    <Edit3 className="w-4 h-4" /> Required Corrections
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_sif_level" className="text-xs text-muted-foreground">Corrected SIF Level</Label>
                      <Select value={correctedSifLevel || 'none'} onValueChange={(v) => setCorrectedSifLevel(v === 'none' ? '' : v as SIFLevel)}>
                        <SelectTrigger id="corrected_sif_level" className="h-9 bg-background/50 border-border/50"><SelectValue placeholder="Leave unchanged" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Leave unchanged</SelectItem>
                          <SelectItem value="NON_SIF">Non-SIF</SelectItem>
                          <SelectItem value="LOW">Low</SelectItem>
                          <SelectItem value="MEDIUM">Medium</SelectItem>
                          <SelectItem value="HIGH">High</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_barrier_status" className="text-xs text-muted-foreground">Corrected Barrier Status</Label>
                      <Select value={correctedBarrierStatus || 'none'} onValueChange={(v) => setCorrectedBarrierStatus(v === 'none' ? '' : v as BarrierStatus)}>
                        <SelectTrigger id="corrected_barrier_status" className="h-9 bg-background/50 border-border/50"><SelectValue placeholder="Leave unchanged" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">Leave unchanged</SelectItem>
                          <SelectItem value="EFFECTIVE">Effective</SelectItem>
                          <SelectItem value="FAILED">Failed</SelectItem>
                          <SelectItem value="MISSING">Missing</SelectItem>
                          <SelectItem value="UNKNOWN">Unknown</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="corrected_lsr" className="text-xs text-muted-foreground">Corrected Life Saving Rule</Label>
                    <input id="corrected_lsr" className="flex h-9 w-full rounded-md border border-border/50 bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground" value={correctedLsr} onChange={e => setCorrectedLsr(e.target.value)} placeholder="Leave unchanged" />
                  </div>

                  <div className="space-y-3 pt-4 border-t border-orange-500/20">
                    <p className="text-xs font-semibold text-foreground">Precursor Corrections</p>
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_activity" className="text-xs text-muted-foreground">Activity</Label>
                      <input id="corrected_activity" className="flex h-9 w-full rounded-md border border-border/50 bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground" value={correctedActivity} onChange={e => setCorrectedActivity(e.target.value)} placeholder="Leave unchanged" />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_hazard" className="text-xs text-muted-foreground">Hazard</Label>
                      <input id="corrected_hazard" className="flex h-9 w-full rounded-md border border-border/50 bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground" value={correctedHazard} onChange={e => setCorrectedHazard(e.target.value)} placeholder="Leave unchanged" />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_barrier" className="text-xs text-muted-foreground">Barrier</Label>
                      <input id="corrected_barrier" className="flex h-9 w-full rounded-md border border-border/50 bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground" value={correctedBarrier} onChange={e => setCorrectedBarrier(e.target.value)} placeholder="Leave unchanged" />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="corrected_barrier_failure" className="text-xs text-muted-foreground">Barrier Failure Details</Label>
                      <input id="corrected_barrier_failure" className="flex h-9 w-full rounded-md border border-border/50 bg-background/50 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground" value={correctedBarrierFailure} onChange={e => setCorrectedBarrierFailure(e.target.value)} placeholder="Leave unchanged" />
                    </div>
                  </div>

                </div>
              )}

              <div className="space-y-1.5 pt-4">
                <Label htmlFor="reviewer_comment" className="text-sm font-medium text-foreground">Reviewer Comments</Label>
                <Textarea id="reviewer_comment" value={comment} onChange={(e) => setComment(e.target.value)} rows={4} placeholder="Add your rationale for this decision..." className="resize-none bg-muted/20 border-border/50 text-foreground" />
              </div>
            </div>

          </div>
        </div>

        <DialogFooter className="px-6 py-4 border-t border-border bg-muted/20 shrink-0">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} variant={decision === 'REJECT' ? 'destructive' : 'default'} className="px-8">
            {mutation.isPending ? 'Saving...' : `Submit ${decision}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function ReviewQueuePage() {
  const { user } = useAuth();
  const [statusFilter, setStatusFilter] = useState<ReviewStatusFilter>('PENDING');
  const [selectedReview, setSelectedReview] = useState<ReviewQueueItem | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const reviewsQ = useQuery({
    queryKey: ['reviews', statusFilter],
    queryFn: () => reviewsApi.list({ page: 1, page_size: 50, status: statusFilter }),
  });

  const canDecide = user != null && ['ADMIN', 'HSE_MANAGER', 'REVIEWER'].includes(user.role);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Human Review Queue</h1>
          <p className="text-sm text-muted-foreground mt-0.5">AI-flagged reports awaiting expert validation</p>
        </div>
      </div>

      <div className="glass-card p-4 flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Status:</span>
        <div className="flex gap-2">
          {(['PENDING', 'REVIEWED', 'ALL'] as ReviewStatusFilter[]).map((s) => (
            <Button key={s} variant={statusFilter === s ? 'default' : 'outline'} size="sm" onClick={() => setStatusFilter(s)}
              className="gap-1.5">
              {s === 'PENDING' && <Clock className="h-3.5 w-3.5" />}
              {s === 'REVIEWED' && <CheckCircle className="h-3.5 w-3.5" />}
              {s === 'ALL' && <XCircle className="h-3.5 w-3.5" />}
              {s}
            </Button>
          ))}
        </div>
      </div>

      <div className="glass-card overflow-hidden">
        {reviewsQ.isLoading && <div className="p-6 space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}</div>}
        {reviewsQ.isError && <ErrorState title="Could not load reviews" onRetry={reviewsQ.refetch} />}
        {reviewsQ.data?.length === 0 && <EmptyState title="No reviews found" description="Try a different status filter." icon={<CheckSquare className="h-7 w-7" />} />}
        {reviewsQ.data && reviewsQ.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" aria-label="Review queue">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Report ID</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Decision</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Confidence</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Narrative (preview)</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Reviewed At</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Action</th>
                </tr>
              </thead>
              <tbody>
                {reviewsQ.data.map((review) => (
                  <tr key={review.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-primary">{review.report_id}</td>
                    <td className="px-4 py-3"><ReviewDecisionBadge decision={review.decision} /></td>
                    <td className="px-4 py-3 text-sm font-semibold">
                      {review.overall_confidence != null ? `${(review.overall_confidence * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td className="px-4 py-3 max-w-xs"><p className="text-sm text-foreground line-clamp-2">{review.report_text}</p></td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {review.reviewed_at ? (() => { try { return format(new Date(review.reviewed_at), 'dd MMM yyyy HH:mm'); } catch { return review.reviewed_at; } })() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <Button variant={review.decision === 'PENDING' ? 'default' : 'outline'} size="sm"
                        onClick={() => { setSelectedReview(review); setDialogOpen(true); }}
                        disabled={!canDecide} className="gap-1.5">
                        {review.decision === 'PENDING' ? <><CheckSquare className="h-3.5 w-3.5" />Decide</> : <><Edit3 className="h-3.5 w-3.5" />View</>}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!canDecide && <p className="text-xs text-muted-foreground text-center">Your role (<strong>{user?.role}</strong>) is view-only. Only ADMIN, HSE_MANAGER, and REVIEWER can submit decisions.</p>}

      <DecisionDialog review={selectedReview} open={dialogOpen} onClose={() => { setDialogOpen(false); setSelectedReview(null); }} />
    </div>
  );
}
