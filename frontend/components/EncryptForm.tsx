"use client";

import { useRef, useState } from "react";
import { encrypt } from "../lib/api";
import { copyToClipboard } from "../lib/copy";
import GlassCard from "./GlassCard";
import { CopyIcon, EyeIcon, EyeOffIcon, LoaderIcon, LockIcon } from "./Icons";
import { StatusToast } from "./StatusToast";

type Toast = { message: string; tone: "success" | "error" };

type EncryptFormProps = {
  password: string;
  onPasswordChange: (value: string) => void;
};

export default function EncryptForm({ password, onPasswordChange }: EncryptFormProps) {
  const [plaintext, setPlaintext] = useState("");
  const [encryptedMessage, setEncryptedMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const plaintextRef = useRef<HTMLTextAreaElement | null>(null);

  const showToast = (payload: Toast) => {
    setToast(payload);
    setTimeout(() => setToast(null), 2400);
  };

  const handleEncrypt = async (e?: React.FormEvent<HTMLFormElement>) => {
    e?.preventDefault();
    if (!plaintext.trim() || !password.trim()) {
  showToast({ tone: "error", message: "Add text and password to encrypt." });
  return;
}

if (password.length < 8) {
  showToast({ tone: "error", message: "Password must be at least 8 characters." });
  return;
}
    try {
      setLoading(true);
      const { data } = await encrypt(plaintext.trim(), password);
      setEncryptedMessage(data?.encoded ?? data?.ciphertext ?? "");
      showToast({ tone: "success", message: "Encrypted successfully." });
    } catch {
      showToast({ tone: "error", message: "Password must be at least 8 characters." });
    } finally {
      setLoading(false);
    }
  };

  const copyResult = async () => {
    if (!encryptedMessage) {
      showToast({ tone: "error", message: "No encrypted message to copy." });
      return;
    }

    try {
      const copied = await copyToClipboard(encryptedMessage);
      if (!copied) throw new Error("Clipboard unavailable");
      if (navigator.vibrate) navigator.vibrate(20);
      showToast({ tone: "success", message: "Copied to clipboard." });
    } catch {
      showToast({ tone: "error", message: "Copy failed. Use manual select and copy." });
    }
  };

  return (
    <GlassCard
      id="encrypt"
      title="Encrypt Text"
      icon={<LockIcon className="h-5 w-5" />}
    >
      <form className="space-y-6" onSubmit={handleEncrypt}>
        <div className="grid gap-2">
          <label className="input-label" htmlFor="plaintext">
            Plain text
          </label>
          <textarea
            ref={plaintextRef}
            id="plaintext"
            className="textarea min-h-[160px] select-text"
            placeholder="Type or paste text to encrypt..."
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            value={plaintext}
            onChange={(e) => {
              const next = e.target.value;
              setPlaintext(next);
              const el = plaintextRef.current;
              if (!el) return;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 320)}px`;
            }}
            onPaste={() => {
              requestAnimationFrame(() => {
                const el = plaintextRef.current;
                if (!el) return;
                setPlaintext(el.value);
                el.style.height = "auto";
                el.style.height = `${Math.min(el.scrollHeight, 320)}px`;
              });
            }}
          />
        </div>

        <div className="grid gap-2">
          <label className="input-label" htmlFor="encrypt-password">
            Password
          </label>
          <div className="relative">
            <input
              id="encrypt-password"
              type={showPassword ? "text" : "password"}
              className="input-field pr-12"
              placeholder="Enter password"
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8b949e] active:scale-95"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOffIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
            </button>
          </div>
        </div>

        <div className="sticky-action">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? <LoaderIcon className="h-4 w-4 animate-spin" /> : null}
            {loading ? "Encrypting..." : "Encrypt"}
          </button>
        </div>

        <div className="result-panel">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs uppercase tracking-wide text-[#8b949e]">Encrypted text</span>
            <button type="button" className="btn-ghost" onClick={copyResult} disabled={!encryptedMessage}>
              <CopyIcon className="h-4 w-4" />
              Copy
            </button>
          </div>
          <pre className={`result-text ${encryptedMessage ? "text-[#e6edf3]" : "text-[#8b949e]"}`}>
            {encryptedMessage || "Encrypted text will appear here."}
          </pre>
        </div>
      </form>

      {toast ? <StatusToast message={toast.message} tone={toast.tone} /> : null}
    </GlassCard>
  );
}
