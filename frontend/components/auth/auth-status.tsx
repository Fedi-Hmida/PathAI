"use client";

import Link from "next/link";
import { LogIn, User } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { cn } from "@/lib/utils";

export function AuthStatus({ open }: { open: boolean }) {
  const { status, user } = useAuth();

  if (status === "loading") {
    return null;
  }

  if (status === "authenticated" && user) {
    return (
      <Link
        href="/account"
        title={open ? undefined : user.email}
        className="text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium"
      >
        <User className="size-4 flex-none" />
        <span
          className={cn(
            "overflow-hidden truncate whitespace-nowrap",
            open ? "max-w-[160px] opacity-100" : "max-w-0 opacity-0",
          )}
        >
          {user.email}
        </span>
      </Link>
    );
  }

  return (
    <Link
      href="/login"
      title={open ? undefined : "Sign in"}
      className="text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium"
    >
      <LogIn className="size-4 flex-none" />
      <span
        className={cn(
          "overflow-hidden whitespace-nowrap",
          open ? "max-w-[160px] opacity-100" : "max-w-0 opacity-0",
        )}
      >
        Sign in
      </span>
    </Link>
  );
}
