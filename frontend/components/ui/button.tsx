import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils/cn";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { 
  variant?: ButtonVariant; 
  pending?: boolean;
  asChild?: boolean;
}

const variants: Record<ButtonVariant, string> = {
  primary: "bg-slate-950 text-white hover:bg-slate-800", 
  secondary: "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50",
  danger: "bg-red-700 text-white hover:bg-red-800", 
  ghost: "text-slate-700 hover:bg-slate-100",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", pending = false, disabled, asChild = false, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp 
        className={cn(
          "inline-flex min-h-10 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600",
          "disabled:cursor-not-allowed disabled:opacity-60",
          variants[variant], 
          className
        )} 
        disabled={disabled || pending} 
        aria-disabled={disabled || pending}
        ref={ref}
        {...props}
      >
        {pending && !asChild ? <Spinner size="sm" /> : null}
        {asChild ? children : <>{pending ? null : children}</>}
      </Comp>
    );
  }
);
Button.displayName = "Button";
