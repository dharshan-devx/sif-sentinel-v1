import { Alert } from "@/components/ui/alert";
export function ForbiddenState({ description = "Your account is signed in, but does not have permission for this action." }: { description?: string }) { return <Alert title="Access denied" tone="warning">{description}</Alert>; }
