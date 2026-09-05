"use client";
import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const Sheet = DialogPrimitive.Root;
const SheetTrigger = DialogPrimitive.Trigger;
const SheetClose = DialogPrimitive.Close;
const SheetTitle = DialogPrimitive.Title;
const SheetDescription = DialogPrimitive.Description;
const SheetHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => <div className={cn("flex flex-col gap-1.5 text-left", className)} {...props} />;
const SheetContent = React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>, React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>>(({ className, children, ...props }, ref) => <DialogPrimitive.Portal><DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-slate-950/45 data-[state=closed]:animate-none" /><DialogPrimitive.Content ref={ref} className={cn("fixed inset-y-0 left-0 z-50 flex w-[min(20rem,calc(100%-2.5rem))] flex-col border-r border-border bg-background p-5 shadow-xl focus:outline-none", className)} {...props}>{children}<DialogPrimitive.Close className="absolute right-4 top-4 rounded-md p-1 text-muted-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><X className="size-4" aria-hidden="true" /><span className="sr-only">Close navigation</span></DialogPrimitive.Close></DialogPrimitive.Content></DialogPrimitive.Portal>);
SheetContent.displayName = "SheetContent";
export { Sheet, SheetClose, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger };
