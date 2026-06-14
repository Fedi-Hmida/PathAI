export type DashboardDataMode = "mock" | "backend" | "offline";

export type DashboardRunState = {
  adaptationId: string | null;
  curriculumId: string | null;
  dataMode: DashboardDataMode;
  lastUpdatedAt: string;
  quizId: string | null;
  sessionId: string | null;
};

export const DASHBOARD_RUN_STATE_KEY = "pathai.dashboardRun.v1";
const DASHBOARD_RUN_STATE_TTL_MS = 1000 * 60 * 60 * 12;

const defaultRunState: DashboardRunState = {
  adaptationId: null,
  curriculumId: null,
  dataMode: "mock",
  lastUpdatedAt: new Date(0).toISOString(),
  quizId: null,
  sessionId: null
};

export function getDashboardRunState(): DashboardRunState {
  if (!canUseStorage()) {
    return { ...defaultRunState };
  }

  const raw = window.localStorage.getItem(DASHBOARD_RUN_STATE_KEY);
  if (!raw) {
    return { ...defaultRunState };
  }

  try {
    return normalizeRunState(JSON.parse(raw));
  } catch {
    clearDashboardRunState();
    return { ...defaultRunState };
  }
}

export function setDashboardRunState(state: DashboardRunState): DashboardRunState {
  const normalized = normalizeRunState(state);
  if (canUseStorage()) {
    window.localStorage.setItem(DASHBOARD_RUN_STATE_KEY, JSON.stringify(normalized));
  }
  return normalized;
}

export function updateDashboardRunState(
  patch: Partial<Omit<DashboardRunState, "lastUpdatedAt">> = {}
): DashboardRunState {
  const current = getDashboardRunState();
  return setDashboardRunState({
    ...current,
    ...patch,
    lastUpdatedAt: new Date().toISOString()
  });
}

export function clearDashboardRunState(): void {
  if (canUseStorage()) {
    window.localStorage.removeItem(DASHBOARD_RUN_STATE_KEY);
  }
}

export function isDashboardRunStateExpired(state: DashboardRunState): boolean {
  if (state.dataMode === "mock") {
    return false;
  }

  const updatedAt = Date.parse(state.lastUpdatedAt);
  if (Number.isNaN(updatedAt)) {
    return true;
  }

  return Date.now() - updatedAt > DASHBOARD_RUN_STATE_TTL_MS;
}

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function normalizeRunState(value: unknown): DashboardRunState {
  if (!isRecord(value)) {
    return { ...defaultRunState };
  }

  const dataMode = parseDataMode(value.dataMode);
  return {
    adaptationId: parseNullableString(value.adaptationId),
    curriculumId: parseNullableString(value.curriculumId),
    dataMode,
    lastUpdatedAt: parseString(value.lastUpdatedAt) ?? new Date().toISOString(),
    quizId: parseNullableString(value.quizId),
    sessionId: parseNullableString(value.sessionId)
  };
}

function parseDataMode(value: unknown): DashboardDataMode {
  return value === "backend" || value === "offline" || value === "mock" ? value : "mock";
}

function parseNullableString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function parseString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
