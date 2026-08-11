"use client";

import { useRef, useState } from "react";
import { decrypt } from "../lib/api";
import { copyToClipboard } from "../lib/copy";
import GlassCard from "./GlassCard";
import { CopyIcon, EyeIcon, EyeOffIcon, LoaderIcon, UnlockIcon } from "./Icons";
import { StatusToast } from "./StatusToast";

type Toast = { message: string; tone: "success" | "error" };

type DecryptFormProps = {
  password: string;
  onPasswordChange: (value: string) => void;
};

export default function DecryptForm({ password, onPasswordChange }: DecryptFormProps) {
  const [encryptedMessage, setEncryptedMessage] = useState("");
  const [plaintext, setPlaintext] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);
  const [error, setError] = useState("");
  const encryptedRef = useRef<HTMLTextAreaElement | null>(null);

  const showToast = (payload: Toast) => {
    setToast(payload);
    setTimeout(() => setToast(null), 2400);
  };

  const handleDecrypt = async (e?: React.FormEvent<HTMLFormElement>) => {
    e?.preventDefault();
    setError("");
    if (!encryptedMessage.trim() || !password.trim()) {
      showToast({ tone: "error", message: "Encrypted message and password are required." });
      return;
    }
    try {
      setLoading(true);
      const { data } = await decrypt(encryptedMessage.trim(), password);

if (data?.success === false) {
  setPlaintext("");
  setError("Invalid password or encrypted text.");
  showToast({ tone: "error", message: "Invalid password or encrypted text." });
  return;
}

setPlaintext(data?.plaintext ?? "");
showToast({ tone: "success", message: "Decryption successful." });
    } catch {
      setPlaintext("");
      setError("Wrong password or invalid encrypted message. Decryption failed.");
      showToast({ tone: "error", message: "Decryption failed." });
    } finally {
      setLoading(false);
    }
  };

  const copyPlaintext = async () => {
    if (!plaintext) {
      showToast({ tone: "error", message: "No plaintext to copy." });
      return;
    }

    try {
      const copied = await copyToClipboard(plaintext);
      if (!copied) throw new Error("Clipboard unavailable");
      if (navigator.vibrate) navigator.vibrate(20);
      showToast({ tone: "success", message: "Copied to clipboard." });
    } catch {
      showToast({ tone: "error", message: "Copy failed. Use manual select and copy." });
    }
  };

  return (
    <GlassCard
      id="decrypt"
      title="Decrypt Text"
      icon={<UnlockIcon className="h-5 w-5" />}
    >
      <form className="space-y-6" onSubmit={handleDecrypt}>
        <div className="grid gap-2">
          <label className="input-label" htmlFor="encrypted-message">
            Encrypted text
          </label>
          <textarea
            ref={encryptedRef}
            id="encrypted-message"
            className="textarea min-h-[160px] select-text"
            placeholder="Paste the full encrypted message..."
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            value={encryptedMessage}
            onChange={(e) => {
              const next = e.target.value;
              setEncryptedMessage(next);
              const el = encryptedRef.current;
              if (!el) return;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 300)}px`;
            }}
            onPaste={() => {
              requestAnimationFrame(() => {
                const el = encryptedRef.current;
                if (!el) return;
                setEncryptedMessage(el.value);
                el.style.height = "auto";
                el.style.height = `${Math.min(el.scrollHeight, 300)}px`;
              });
            }}
          />
        </div>

        <div className="grid gap-2">
          <label className="input-label" htmlFor="decrypt-password">
            Password
          </label>
          <div className="relative">
            <input
              id="decrypt-password"
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
            {loading ? "Decrypting..." : "Decrypt"}
          </button>
        </div>

        {error ? <div className="rounded-lg border border-[#da3633]/50 bg-[#da3633]/10 px-4 py-3 text-sm text-[#ffa198]">{error}</div> : null}

        <div className="result-panel">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs uppercase tracking-wide text-[#8b949e]">Plaintext result</span>
            <button type="button" className="btn-ghost" onClick={copyPlaintext} disabled={!plaintext}>
              <CopyIcon className="h-4 w-4" />
              Copy
            </button>
          </div>
          <pre className={`result-text ${plaintext ? "text-[#e6edf3]" : "text-[#8b949e]"}`} aria-live="polite">
            {plaintext || "Decrypted text will appear here."}
          </pre>
        </div>
      </form>

      {toast ? <StatusToast message={toast.message} tone={toast.tone} /> : null}
    </GlassCard>
  );
}
