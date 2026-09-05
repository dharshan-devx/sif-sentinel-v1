import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ApiError } from "@/lib/api";
export function ErrorState({ error, onRetry, title = "Something went wrong" }: { error?: unknown; onRetry?: () => void; title?: string }) { const apiError = error instanceof ApiError ? error : undefined; const message = apiError?.message ?? "We could not complete this request. Please try again."; return <Alert variant="destructive" aria-live="assertive"><AlertTriangle className="size-4" aria-hidden="true" /><AlertTitle>{title}</AlertTitle><AlertDescription><p>{message}</p>{apiError?.requestId ? <p className="mt-2 text-xs">Support reference: {apiError.requestId}</p> : null}{onRetry ? <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}><RefreshCw className="size-3.5" aria-hidden="true" />Try again</Button> : null}</AlertDescription></Alert>; }
