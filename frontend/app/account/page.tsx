"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { RequireAuth } from "@/components/auth/require-auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AccountPage() {
  return (
    <RequireAuth>
      <AccountView />
    </RequireAuth>
  );
}

function AccountView() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [signingOut, setSigningOut] = React.useState(false);

  async function handleLogout() {
    setSigningOut(true);
    try {
      await logout();
      router.replace("/login");
    } finally {
      setSigningOut(false);
    }
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Account
        </span>
        <h1 className="font-goal text-foreground mt-1 text-lg font-medium">Your account</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Signed in</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div>
            <span className="text-muted-foreground text-xs">Email</span>
            <p className="text-foreground text-sm font-medium">{user.email}</p>
          </div>
          <div>
            <span className="text-muted-foreground text-xs">Member since</span>
            <p className="text-foreground text-sm font-medium">
              {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleLogout}
            disabled={signingOut}
            className="mt-2 w-fit"
          >
            {signingOut ? "Signing out..." : "Sign out"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
