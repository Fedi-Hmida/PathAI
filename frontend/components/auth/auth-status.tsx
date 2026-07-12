"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogIn, LogOut, User, UserPlus } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { CollapsingLabel } from "@/components/layout/sidebar-primitives";
import { cn } from "@/lib/utils";

const ROW_CLASSES =
  "text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium";

export function AuthStatus({ open }: { open: boolean }) {
  const { status, user, logout } = useAuth();
  const router = useRouter();
  const [signingOut, setSigningOut] = React.useState(false);

  if (status === "loading") {
    return null;
  }

  async function handleLogout(event: React.MouseEvent) {
    event.preventDefault();
    setSigningOut(true);
    try {
      await logout();
      router.replace("/login");
    } finally {
      setSigningOut(false);
    }
  }

  if (status === "authenticated" && user) {
    return (
      <div className="flex items-center gap-1">
        <Link
          href="/account"
          title={open ? undefined : user.email}
          className={cn(ROW_CLASSES, "min-w-0 flex-1")}
        >
          <User className="size-4 flex-none" />
          <span
            className={cn(
              "overflow-hidden truncate whitespace-nowrap",
              open ? "max-w-[120px] opacity-100" : "max-w-0 opacity-0",
            )}
          >
            {user.email}
          </span>
        </Link>
        <button
          type="button"
          onClick={handleLogout}
          disabled={signingOut}
          title="Log out"
          aria-label="Log out"
          className="text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex-none rounded-lg p-2 disabled:opacity-50"
        >
          <LogOut className="size-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <Link href="/login" title={open ? undefined : "Sign in"} className={ROW_CLASSES}>
        <LogIn className="size-4 flex-none" />
        <CollapsingLabel open={open}>Sign in</CollapsingLabel>
      </Link>
      <Link href="/register" title={open ? undefined : "Sign up"} className={ROW_CLASSES}>
        <UserPlus className="size-4 flex-none" />
        <CollapsingLabel open={open}>Sign up</CollapsingLabel>
      </Link>
    </div>
  );
}
