import React, { useEffect, useMemo, useRef, useState } from 'react';
import { GOOGLE_CLIENT_ID, isGoogleLoginConfigured } from '../config/googleClient';

type GoogleLoginButtonProps = {
  onCredential: (credential: string) => Promise<void>;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
};

const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

const ensureGoogleScript = () => {
  if (document.querySelector(`script[src="${GOOGLE_SCRIPT_SRC}"]`)) {
    return;
  }
  const script = document.createElement('script');
  script.src = GOOGLE_SCRIPT_SRC;
  script.async = true;
  script.defer = true;
  script.dataset.googleIdentity = 'true';
  document.head.appendChild(script);
};

export const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({
  onCredential,
  disabled = false,
  loading = false,
  className,
}) => {
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [buttonRendered, setButtonRendered] = useState(false);

  useEffect(() => {
    if (!isGoogleLoginConfigured) {
      return;
    }

    ensureGoogleScript();

    const handleLoad = () => {
      setScriptReady(true);
      if (scriptEl) {
        scriptEl.dataset.loaded = 'true';
      }
    };
    const scriptEl = document.querySelector<HTMLScriptElement>(
      `script[src="${GOOGLE_SCRIPT_SRC}"]`
    );

    const handleError = () => setScriptReady(false);

    if (scriptEl?.dataset.loaded === 'true') {
      setScriptReady(true);
    } else if (scriptEl) {
      scriptEl.addEventListener('load', handleLoad);
      scriptEl.addEventListener('error', handleError);
    }

    return () => {
      scriptEl?.removeEventListener('load', handleLoad);
      scriptEl?.removeEventListener('error', handleError);
    };
  }, []);

  useEffect(() => {
    if (!scriptReady || !isGoogleLoginConfigured || !buttonRef.current) {
      return;
    }

    if (!window.google?.accounts?.id) {
      return;
    }

    const callback = (response: google.accounts.id.CredentialResponse) => {
      if (response.credential) {
        void onCredential(response.credential);
      }
    };

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback,
      cancel_on_tap_outside: true,
      auto_select: false,
    });

    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      width: 300,
    });

    setButtonRendered(true);

    return () => {
      window.google?.accounts.id.cancel();
      buttonRef.current?.replaceChildren();
      setButtonRendered(false);
    };
  }, [onCredential, scriptReady]);

  const containerClass = useMemo(() => {
    const base = 'relative w-full';
    return className ? `${base} ${className}` : base;
  }, [className]);

  if (!isGoogleLoginConfigured) {
    return (
      <p className="text-sm text-gray-500">
        Google login is not configured. Add a client_secret JSON file to the frontend directory or
        set the VITE_GOOGLE_CLIENT_ID environment variable.
      </p>
    );
  }

  return (
    <div className={containerClass}>
      <div ref={buttonRef} className="flex justify-center" />
      {(!buttonRendered || loading) && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 rounded-lg">
          <span className="text-sm text-gray-600">
            {loading ? 'Signing in with Google…' : 'Loading Google sign-in…'}
          </span>
        </div>
      )}
      {disabled && !loading && (
        <div className="absolute inset-0 bg-white/60 rounded-lg" aria-hidden="true" />
      )}
    </div>
  );
};
