export function getApiBase(): string {
  const override = String(import.meta.env.VITE_API_URL ?? "").trim();

  if (override) {
    return override.replace(/\/$/, "");
  }

  return "/api";
}
