import { getApiBase } from "@/api/base";
import { mockLoginRequest, type UserInfo } from "@/api/authApi";
import { useEffect, useMemo, useState } from "react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  externalError?: string;
  isFinalizing?: boolean;
  onMockLogin?: (token: string, user: UserInfo) => void;
}

const API_BASE = getApiBase();
const PERSONAL_DATA_POLICY_URL = "/legal/pdn-consent.pdf";
const SBER_PARAMS_MAX_AGE_MS = 8 * 60 * 1000;

type SberParamsResponse = {
  authorize_url: string;
  client_id: string;
  redirect_uri: string;
  scopes: string;
  response_type: string;
  state: string;
  nonce: string;
};

type CachedSberParams = {
  fetchedAt: number;
  value: SberParamsResponse;
};

let cachedSberParams: CachedSberParams | null = null;
let sberParamsPromise: Promise<SberParamsResponse> | null = null;

function makeUrl(value: string): URL {
  try {
    return new URL(value);
  } catch {
    if (typeof window !== "undefined") {
      return new URL(value, window.location.origin);
    }
    throw new Error("Invalid URL");
  }
}

function normalizeAuthError(err: unknown, fallbackMessage: string): string {
  const rawMessage = err instanceof Error ? err.message : String(err);

  if (/Failed to construct 'URL'|Invalid URL/i.test(rawMessage)) {
    return "Не удалось подготовить ссылку для входа в Sber ID. Попробуйте обновить страницу или повторите позже.";
  }

  return err instanceof Error && err.message ? err.message : fallbackMessage;
}

function hasFreshCachedParams() {
  return (
    cachedSberParams !== null &&
    Date.now() - cachedSberParams.fetchedAt < SBER_PARAMS_MAX_AGE_MS
  );
}

async function requestSberParams(
  signal?: AbortSignal
): Promise<SberParamsResponse> {
  const frontendUrl =
    typeof window === "undefined"
      ? ""
      : `${window.location.origin}${window.location.pathname}`;
  const paramsUrl = makeUrl(`${API_BASE}/auth/sber/params`);

  if (frontendUrl) {
    paramsUrl.searchParams.set("frontend_url", frontendUrl);
  }

  const paramsRes = await fetch(paramsUrl.toString(), {
    method: "GET",
    credentials: "include",
    signal,
  });

  if (!paramsRes.ok) {
    const body = await paramsRes.json().catch(() => null);
    throw new Error(body?.detail ?? "Не удалось получить параметры Сбер ID");
  }

  return (await paramsRes.json()) as SberParamsResponse;
}

function saveCachedParams(params: SberParamsResponse) {
  cachedSberParams = {
    fetchedAt: Date.now(),
    value: params,
  };

  return params;
}

async function getSberParams(signal?: AbortSignal): Promise<SberParamsResponse> {
  if (hasFreshCachedParams()) {
    return cachedSberParams!.value;
  }

  if (sberParamsPromise) {
    return sberParamsPromise;
  }

  const request = requestSberParams(signal).then(saveCachedParams);
  sberParamsPromise = request.finally(() => {
    sberParamsPromise = null;
  });

  return sberParamsPromise;
}

function buildSberAuthUrl(params: SberParamsResponse): string {
  const url = makeUrl(params.authorize_url);

  url.searchParams.set("client_id", params.client_id);
  url.searchParams.set("client_type", "PRIVATE");
  url.searchParams.set("nonce", params.nonce);
  url.searchParams.set("redirect_uri", params.redirect_uri);
  url.searchParams.set("response_type", params.response_type);
  url.searchParams.set("scope", params.scopes);
  url.searchParams.set("state", params.state);

  return url.toString();
}

export function preloadSberAuthParams() {
  void getSberParams().catch(() => {
    // Ignore warmup errors; modal shows the actual error later.
  });
}

export default function AuthModal({
  isOpen,
  onClose,
  externalError = "",
  isFinalizing = false,
  onMockLogin,
}: AuthModalProps) {
  const [initError, setInitError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState("");
  const [consentChecked, setConsentChecked] = useState(false);
  const [consentError, setConsentError] = useState(false);
  const [isMockLoading, setIsMockLoading] = useState(false);
  const [mockError, setMockError] = useState("");

  const displayError = initError || externalError;
  const isAuthReady = !!authUrl && !isLoading && !displayError;

  useEffect(() => {
    if (!isOpen) {
      setInitError("");
      setIsLoading(false);
      setAuthUrl("");
      setConsentChecked(false);
      setConsentError(false);
      setMockError("");
      setIsMockLoading(false);
      return;
    }

    if (isFinalizing) {
      setInitError("");
      setIsLoading(false);
      setAuthUrl("");
      return;
    }

    let cancelled = false;
    const controller = new AbortController();

    const loadParams = async () => {
      try {
        setInitError("");
        setIsLoading(true);

        const params = await getSberParams(controller.signal);

        if (cancelled) {
          return;
        }

        setAuthUrl(buildSberAuthUrl(params));
      } catch (err: unknown) {
        if (cancelled || (err instanceof DOMException && err.name === "AbortError")) {
          return;
        }

        console.error("AuthModal: failed to init Sber auth params", err);

        setAuthUrl("");
        setInitError(normalizeAuthError(err, "Не удалось инициализировать Сбер ID"));
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadParams();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [isOpen, isFinalizing]);

  const buttonLabel = useMemo(() => {
    if (isLoading && !authUrl) {
      return "Подготовка входа...";
    }

    return "Войти по Sber ID";
  }, [authUrl, isLoading]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-[2px]"
        onClick={onClose}
      />

      <div
        className="relative z-10 mx-4 w-full max-w-[420px] rounded-[24px] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.14)] fade-in-up"
        style={{
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(255,255,255,0.82) 100%)",
          backdropFilter: "blur(30px) saturate(180%)",
          WebkitBackdropFilter: "blur(30px) saturate(180%)",
          border: "1px solid rgba(255,255,255,0.7)",
        }}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800">Вход через Sber ID</h3>
          <button
            onClick={onClose}
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-2xl border border-white/60 bg-white/45 text-slate-500 transition-colors hover:bg-white/75"
            aria-label="Закрыть"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 6L6 18" />
              <path d="M6 6L18 18" />
            </svg>
          </button>
        </div>

        {isFinalizing ? (
          <div className="py-8">
            <div className="flex flex-col items-center justify-center gap-3 text-center">
              <div className="h-11 w-11 animate-spin rounded-full border-[3px] border-emerald-100 border-t-emerald-500" />
              <div>
                <p className="text-[15px] font-semibold text-slate-800">
                  Завершаем вход...
                </p>
                <p className="mt-1 text-[13px] leading-5 text-slate-500">
                  Подтверждаем вход через Sber ID и создаем сессию.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {onMockLogin && (
              <div className="mt-4 flex flex-col items-center gap-2">
                <button
                  type="button"
                  onClick={async () => {
                    if (!consentChecked) {
                      setConsentError(true);
                      return;
                    }
                    setConsentError(false);
                    if (isMockLoading) return;
                    setMockError("");
                    setIsMockLoading(true);
                    try {
                      const result = await mockLoginRequest();
                      onMockLogin(result.token, result.user);
                    } catch (err: unknown) {
                      console.error("AuthModal: mock login failed", err);
                      setMockError(
                        normalizeAuthError(err, "Не удалось выполнить временный вход")
                      );
                    } finally {
                      setIsMockLoading(false);
                    }
                  }}
                  disabled={isMockLoading}
                  className={`mx-auto flex min-h-[48px] w-full max-w-[320px] items-center justify-center gap-2 rounded-[14px] border border-dashed border-amber-400 bg-amber-50/70 px-5 text-[14px] font-medium text-amber-800 transition-all ${
                    isMockLoading
                      ? "cursor-wait opacity-60"
                      : "cursor-pointer hover:bg-amber-100/80"
                  }`}
                >
                  {isMockLoading ? (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-amber-400/40 border-t-amber-600" />
                  ) : (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                      className="shrink-0 opacity-70"
                    >
                      <circle cx="12" cy="8" r="4" />
                      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
                    </svg>
                  )}
                  <span>Временный вход (без Sber ID)</span>
                </button>
                {mockError && (
                  <p className="text-center text-[12px] text-rose-600">{mockError}</p>
                )}
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="h-px flex-1 bg-slate-200" />
                  <span>или</span>
                  <span className="h-px flex-1 bg-slate-200" />
                </div>
              </div>
            )}

            <div className="mt-2 flex flex-col items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => {
                  if (!consentChecked) {
                    setConsentError(true);
                    return;
                  }

                  setConsentError(false);

                  if (!authUrl) {
                    return;
                  }

                  window.location.href = authUrl;
                }}
                disabled={isLoading || !authUrl}
                className={`mx-auto flex min-h-[56px] w-full max-w-[320px] items-center justify-center gap-3 rounded-[18px] px-6 text-[16px] font-semibold text-white transition-all ${
                  isLoading || !authUrl
                    ? "cursor-wait bg-emerald-500/80 shadow-[0_10px_28px_rgba(16,185,129,0.2)]"
                    : "cursor-pointer bg-[#25a732] shadow-[0_12px_32px_rgba(37,167,50,0.28)] hover:-translate-y-0.5 hover:bg-[#21972d]"
                }`}
              >
                {isLoading && !authUrl ? (
                  <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/35 border-t-white" />
                ) : (
                  <svg
                    width="26"
                    height="26"
                    viewBox="0 0 26 26"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                    className="shrink-0"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M13 0C16.0927 0 18.9337 1.08103 21.1657 2.88421L18.6371 4.74793C17.0315 3.64848 15.0899 3.00354 13 3.00354C7.48924 3.00354 3.00587 7.48999 3.00587 13.0013C3.00587 18.5126 7.48924 22.9965 13 22.9965C18.5134 22.9965 22.9968 18.5126 22.9968 13.0013C22.9968 12.9118 22.9941 12.8223 22.9924 12.7328L25.7912 10.6699C25.9289 11.4245 26 12.2055 26 13.0013C26 20.1807 20.1795 26 13 26C5.82135 26 0 20.1807 0 13.0013C0 5.81931 5.82135 0 13 0ZM23.2856 5.05241C23.9006 5.84651 24.4262 6.71169 24.8456 7.63565L13.0002 16.3673L8.05093 13.2628V9.52921L13.0002 12.6337L23.2856 5.05241Z"
                      fill="white"
                    />
                  </svg>
                )}
                <span>{buttonLabel}</span>
              </button>

              {!isAuthReady && !displayError && (
                <p className="min-h-[20px] text-center text-[12px] text-slate-400">
                  Подготавливаем безопасный переход в Sber ID...
                </p>
              )}
            </div>

            <div
              className={`mt-5 rounded-2xl border px-3 py-3 transition-colors ${
                consentError
                  ? "border-rose-300 bg-rose-50/70"
                  : "border-slate-200/80 bg-white/60"
              }`}
            >
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  checked={consentChecked}
                  onChange={(e) => {
                    setConsentChecked(e.target.checked);
                    if (e.target.checked) {
                      setConsentError(false);
                    }
                  }}
                  className="mt-0.5 h-4 w-4 shrink-0 accent-emerald-500"
                />
                <span className="text-[12px] leading-5 text-slate-600">
                  Я даю согласие на обработку персональных данных и подтверждаю,
                  что ознакомился(ась) с{" "}
                  <a
                    href={PERSONAL_DATA_POLICY_URL}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-emerald-700 underline underline-offset-2"
                  >
                    текстом согласия
                  </a>
                  .
                </span>
              </label>
            </div>
          </>
        )}

        {consentError && !isFinalizing && (
          <div className="mt-2 rounded-xl border border-rose-200/60 bg-rose-50/60 px-3 py-2 text-[12px] text-rose-600">
            Чтобы продолжить, поставьте галочку согласия на обработку персональных данных.
          </div>
        )}

        {displayError && (
          <div className="mt-4 rounded-xl border border-rose-200/60 bg-rose-50/60 px-3 py-2 text-[12px] text-rose-600">
            {displayError}
          </div>
        )}
      </div>
    </div>
  );
}
