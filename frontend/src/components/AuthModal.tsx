import { useEffect, useRef, useState } from "react";
import { loginRequest } from "@/api/authApi";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (token: string, userName: string) => void;
}

const API_BASE = import.meta.env.VITE_API_URL || "";
const PERSONAL_DATA_POLICY_URL = "/legal/pdn-consent.pdf";

type SberParamsResponse = {
  client_id: string;
  redirect_uri: string;
  scopes: string;
  response_type: string;
  state: string;
  nonce: string;
};

type SberidSDKInstance = {
  init: () => Promise<unknown>;
};

type SberidSDKConstructor = new (params: Record<string, unknown>) => SberidSDKInstance;

declare global {
  interface Window {
    SberidSDK?: SberidSDKConstructor;
  }
}

function loadSberSdk(): Promise<SberidSDKConstructor> {
  return new Promise((resolve, reject) => {
    if (window.SberidSDK) {
      resolve(window.SberidSDK);
      return;
    }

    if (!document.getElementById("sberid-css")) {
      const link = document.createElement("link");
      link.id = "sberid-css";
      link.rel = "stylesheet";
      link.href = "https://id-ift.sber.ru/sdk/web/styles/common.css";
      document.head.appendChild(link);
    }

    const existingScript = document.getElementById("sberid-sdk-script");
    if (existingScript) {
      const waitForSdk = () => {
        if (window.SberidSDK) {
          resolve(window.SberidSDK);
        } else {
          setTimeout(waitForSdk, 50);
        }
      };
      waitForSdk();
      return;
    }

    const script = document.createElement("script");
    script.id = "sberid-sdk-script";
    script.src = "https://id-ift.sber.ru/sdk/web/sberid-sdk.production.js";
    script.async = true;
    script.onload = () => {
      if (window.SberidSDK) {
        resolve(window.SberidSDK);
      } else {
        reject(new Error("SberID SDK загружен, но не инициализировался"));
      }
    };
    script.onerror = () => reject(new Error("Не удалось загрузить SberID SDK"));
    document.body.appendChild(script);
  });
}

export default function AuthModal({
  isOpen,
  onClose,
  onAuthSuccess,
}: AuthModalProps) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sdkLoading, setSdkLoading] = useState(false);
  const [isSdkReady, setIsSdkReady] = useState(false);

  const [consentChecked, setConsentChecked] = useState(false);
  const [consentError, setConsentError] = useState(false);

  const sberIdContainerRef = useRef<HTMLDivElement>(null);
  const initIdRef = useRef(0);

  const requireConsent = (): boolean => {
    if (consentChecked) {
      setConsentError(false);
      return true;
    }

    setConsentError(true);
    return false;
  };

  useEffect(() => {
    if (!isOpen) {
      setError("");
      setLoading(false);
      setSdkLoading(false);
      setIsSdkReady(false);
      setConsentChecked(false);
      setConsentError(false);
      if (sberIdContainerRef.current) {
        sberIdContainerRef.current.innerHTML = "";
      }
      return;
    }

    let cancelled = false;
    const currentInitId = ++initIdRef.current;

    const initSdkButton = async () => {
      try {
        setSdkLoading(true);
        setError("");

        const [SberidSDK, paramsRes] = await Promise.all([
          loadSberSdk(),
          fetch(`${API_BASE}/auth/sber/params`, {
            method: "GET",
            credentials: "include",
          }),
        ]);

        if (!paramsRes.ok) {
          const body = await paramsRes.json().catch(() => null);
          throw new Error(
            body?.detail ?? "Не удалось получить параметры Сбер ID"
          );
        }

        const params = (await paramsRes.json()) as SberParamsResponse;

        if (
          cancelled ||
          currentInitId !== initIdRef.current ||
          !sberIdContainerRef.current
        ) {
          return;
        }

        sberIdContainerRef.current.innerHTML = "";

        const sdk = new SberidSDK({
          baseUrl: "https://id-ift.sber.ru",
          oidc: {
            client_id: params.client_id,
            client_type: "PRIVATE",
            nonce: params.nonce,
            redirect_uri: params.redirect_uri,
            state: params.state,
            scope: params.scopes,
            response_type: params.response_type,
            name: "ИИ-помощник по социальной поддержке",
          },
          container: sberIdContainerRef.current,
          display: "page",
          generateState: false,
          notification: { enable: false },
          personalization: false,
          fastLogin: { enable: false },
          buttonProps: { type: "default" },
        });

        await sdk.init();
        setIsSdkReady(true);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Не удалось инициализировать Сбер ID"
          );
        }
      } finally {
        if (!cancelled) {
          setSdkLoading(false);
        }
      }
    };

    void initSdkButton();

    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLogin = async () => {
    if (loading || sdkLoading) return;
    if (!requireConsent()) return;

    setError("");
    setLoading(true);

    try {
      const data = await loginRequest();
      onAuthSuccess(data.token, "Иванов Иван");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Произошла ошибка");
    } finally {
      setLoading(false);
    }
  };

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
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-800">Вход в систему</h3>
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

        <button
          type="button"
          onClick={handleLogin}
          disabled={loading}
          className={`w-full cursor-pointer rounded-2xl py-3.5 text-[15px] font-semibold transition-all ${
            loading
              ? "cursor-not-allowed bg-slate-200/80 text-slate-400"
              : "bg-emerald-500 text-white shadow-[0_8px_24px_rgba(16,185,129,0.3)] hover:-translate-y-0.5 hover:bg-emerald-600"
          }`}
        >
          {loading ? "Загрузка..." : "Войти (тестовый аккаунт)"}
        </button>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-200/80" />
          <span className="text-[12px] text-slate-400">или</span>
          <div className="h-px flex-1 bg-slate-200/80" />
        </div>

        <div className="relative min-h-[56px]">
          {!isSdkReady && (
            <div className="absolute inset-0 flex items-center justify-center rounded-2xl border border-slate-200/80 bg-white/70 text-[13px] text-slate-400">
              Подготавливаем кнопку Сбер ID...
            </div>
          )}

          <div
            ref={sberIdContainerRef}
            className={`sberid-btn-container transition-opacity duration-200 ${
              isSdkReady ? "opacity-100" : "opacity-0"
            }`}
          />

          {!consentChecked && (
            <button
              type="button"
              onClick={() => {
                setConsentError(true);
                setError("");
              }}
              className="absolute inset-0 z-10 cursor-pointer rounded-2xl bg-transparent"
              aria-label="Сначала подтвердите согласие на обработку персональных данных"
            />
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

        {consentError && (
          <div className="mt-2 rounded-xl border border-rose-200/60 bg-rose-50/60 px-3 py-2 text-[12px] text-rose-600">
            Чтобы продолжить, поставьте галочку согласия на обработку персональных данных.
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-rose-200/60 bg-rose-50/60 px-3 py-2 text-[12px] text-rose-600">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
