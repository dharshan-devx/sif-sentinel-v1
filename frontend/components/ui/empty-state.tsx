import { Card } from "@/components/ui/card";
export function EmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) { return <Card className="text-center"><h2 className="text-base font-bold">{title}</h2><p className="mx-auto mt-2 max-w-lg text-sm text-slate-600">{description}</p>{action && <div className="mt-4">{action}</div>}</Card>; }
