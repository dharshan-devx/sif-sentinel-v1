import { AlertOctagon, AlertTriangle, CircleAlert, Info } from "lucide-react";
import { Badge } from "./badge";

const severityConfig = {
  CRITICAL: { icon: AlertOctagon, variant: "critical" as const },
  HIGH: { icon: AlertTriangle, variant: "warning" as const },
  MEDIUM: { icon: CircleAlert, variant: "secondary" as const },
  LOW: { icon: Info, variant: "outline" as const },
};
export type Severity = keyof typeof severityConfig;
export function SeverityBadge({ severity }: { severity: Severity }) { const { icon: Icon, variant } = severityConfig[severity]; return <Badge variant={variant}><Icon className="size-3" aria-hidden="true" /><span>{severity}</span></Badge>; }
