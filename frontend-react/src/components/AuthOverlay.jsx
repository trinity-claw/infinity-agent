import React, { useMemo, useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import agentLogo from '../../infinity-agent-logo.png';

const normalizeEmail = (value = '') => value.trim().toLowerCase();
const normalizeText = (value = '') =>
  value
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const deriveUserIdFromEmail = (email) => {
  const normalized = normalizeEmail(email);
  if (!normalized) return 'client_web';
  const sanitized = normalized.replace(/[^a-z0-9]/g, '_').slice(0, 40);
  return `client_${sanitized}`;
};

const isEmailAllowed = ({ email, displayName, allowedEmails, allowedContainsTokens }) => {
  if (!email) return false;

  if (allowedEmails.length === 0 && allowedContainsTokens.length === 0) {
    return true;
  }

  if (allowedEmails.includes(email)) {
    return true;
  }

  if (allowedContainsTokens.length > 0) {
    const localPart = email.split('@')[0] || '';
    const candidate = normalizeText(`${localPart} ${displayName || ''}`);
    const matchesToken = allowedContainsTokens.some((token) => candidate.includes(token));
    if (matchesToken) return true;
  }

  return false;
};

const AuthOverlay = ({ onAuthSuccess }) => {
  const [errorMsg, setErrorMsg] = useState('');
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim();

  const allowedEmails = useMemo(
    () =>
      (import.meta.env.VITE_ALLOWED_EMAILS || '')
        .split(',')
        .map(normalizeEmail)
        .filter(Boolean),
    [],
  );

  const allowedEmailContainsTokens = useMemo(
    () =>
      (import.meta.env.VITE_ALLOWED_EMAIL_CONTAINS || '')
        .split(',')
        .map(normalizeText)
        .filter(Boolean),
    [],
  );

  const handleSuccess = (credentialResponse) => {
    const credential = credentialResponse?.credential;
    if (!credential) {
      setErrorMsg('Não foi possível obter uma credencial válida do Google.');
      return;
    }

    try {
      const decodedUser = jwtDecode(credential);
      const email = normalizeEmail(decodedUser?.email || '');
      if (!email) {
        setErrorMsg('A credencial retornada não contém e-mail.');
        return;
      }

      const displayName = decodedUser?.name?.trim() || '';
      const isAllowed = isEmailAllowed({
        email,
        displayName,
        allowedEmails,
        allowedContainsTokens: allowedEmailContainsTokens,
      });

      if (!isAllowed) {
        setErrorMsg(
          'Acesso restrito. Este e-mail não atende às regras de autorização configuradas.',
        );
        return;
      }

      const profile = {
        email,
        name: displayName || email.split('@')[0],
        picture: decodedUser?.picture || '',
      };

      localStorage.setItem('infinity_auth_token', credential);
      localStorage.setItem('infinity_auth_email', profile.email);
      localStorage.setItem('infinity_auth_name', profile.name);
      localStorage.setItem('infinity_auth_picture', profile.picture);

      if (!localStorage.getItem('infinity_user_id')) {
        localStorage.setItem('infinity_user_id', deriveUserIdFromEmail(profile.email));
      }

      setErrorMsg('');
      onAuthSuccess(profile);
    } catch (error) {
      console.error('Google credential decode error:', error);
      setErrorMsg('Falha ao processar a credencial do Google.');
    }
  };

  const handleError = () => {
    setErrorMsg('Falha na comunicação com o Google.');
  };

  return (
    <div className="auth-overlay">
      <div className="auth-shell">
        <section className="auth-brand-panel">
          <div className="auth-brand-header">
            <img src={agentLogo} alt="Infinity Agent" className="auth-brand-logo" />
            <div className="auth-brand-copy">
              <span className="auth-brand-kicker">Infinity Agent</span>
              <span className="auth-brand-subkicker">AI Swarm Platform</span>
            </div>
          </div>

          <h1 className="auth-brand-title">Central Inteligente de Atendimento InfinitePay</h1>
          <p className="auth-brand-description">
            Acesse a plataforma oficial para operar o swarm de agentes com roteamento automático,
            suporte operacional e handoff humano.
          </p>

          <div className="auth-feature-list">
            <div className="auth-feature-item">
              <span className="auth-feature-dot" />
              <span>Router + especialistas (Knowledge, Support e Sentiment)</span>
            </div>
            <div className="auth-feature-item">
              <span className="auth-feature-dot" />
              <span>RAG com dados InfinitePay e busca web em tempo real</span>
            </div>
            <div className="auth-feature-item">
              <span className="auth-feature-dot" />
              <span>Escalação assistida para atendimento humano</span>
            </div>
          </div>
        </section>

        <section className="auth-login-panel">
          <div className="auth-login-icon">
            <svg viewBox="0 0 64 64" fill="none" aria-hidden="true">
              <circle cx="32" cy="32" r="30" stroke="#00E676" strokeWidth="2" strokeDasharray="4 4" />
              <path d="M20 34L30 44L46 22" stroke="#00E676" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>

          <h2>Entrar na Plataforma</h2>
          <p>Faça login com sua conta Google autorizada para acessar o Infinity Agent.</p>

          {errorMsg && <div className="auth-error">{errorMsg}</div>}

          <div className="auth-btn-wrapper">
            {googleClientId ? (
              <GoogleLogin
                onSuccess={handleSuccess}
                onError={handleError}
                theme="filled_black"
                shape="pill"
                text="signin_with"
                locale="pt-BR"
              />
            ) : (
              <div className="auth-missing-config">
                Defina <code>VITE_GOOGLE_CLIENT_ID</code> no ambiente do frontend.
              </div>
            )}
          </div>

          <p className="auth-footer">
            Acesso permitido apenas para e-mails autorizados por allowlist/padrão.
          </p>
        </section>
      </div>
    </div>
  );
};

export default AuthOverlay;