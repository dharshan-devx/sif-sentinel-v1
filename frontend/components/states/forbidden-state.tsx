import { LockKeyhole } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
export function ForbiddenState({ message = "Your current role does not have permission to view this area." }: { message?: string }) { return <Alert variant="warning"><LockKeyhole className="size-4" aria-hidden="true" /><AlertTitle>Access restricted</AlertTitle><AlertDescription>{message}</AlertDescription></Alert>; }
