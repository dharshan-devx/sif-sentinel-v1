"use client";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { isApiClientError } from "@/lib/api/client";
export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) { const apiError = isApiClientError(error) ? error : null; return <Alert title={apiError?.message ?? "We could not load this information."} tone="danger"><p>Please try again. {apiError?.requestId && <span>Support reference: {apiError.requestId}</span>}</p>{retry && <Button className="mt-3" variant="secondary" type="button" onClick={retry}>Try again</Button>}</Alert>; }
