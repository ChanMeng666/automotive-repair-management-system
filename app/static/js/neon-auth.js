/**
 * Neon Auth Client Integration
 * Handles email+password and Google OAuth authentication via Neon Auth (Better Auth)
 */

// ============ DEBUG LOGGER ============
const _debugLogs = [];
function _createDebugPanel() {
    let panel = document.getElementById('neon-debug-panel');
    if (panel) return panel;

    panel = document.createElement('div');
    panel.id = 'neon-debug-panel';
    panel.style.cssText = 'position:fixed;bottom:0;left:0;right:0;max-height:40vh;overflow-y:auto;' +
        'background:#1a1a2e;color:#0f0;font-family:monospace;font-size:11px;padding:8px 12px;z-index:99999;' +
        'border-top:2px solid #e85d04;white-space:pre-wrap;word-break:break-all;user-select:text;';

    // Toolbar
    const toolbar = document.createElement('div');
    toolbar.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;position:sticky;top:0;background:#1a1a2e;padding:4px 0;z-index:1;';

    const title = document.createElement('span');
    title.style.cssText = 'color:#e85d04;font-weight:bold;font-size:13px;';
    title.textContent = '=== NeonAuth Debug Panel ===';

    const btnGroup = document.createElement('span');
    btnGroup.style.cssText = 'display:flex;gap:6px;';

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy All Logs';
    copyBtn.style.cssText = 'background:#e85d04;color:#fff;border:none;padding:4px 12px;border-radius:4px;' +
        'cursor:pointer;font-family:monospace;font-size:12px;font-weight:bold;';
    copyBtn.addEventListener('click', function() {
        const text = _debugLogs.join('\n');
        navigator.clipboard.writeText(text).then(function() {
            copyBtn.textContent = 'Copied!';
            copyBtn.style.background = '#2ecc71';
            setTimeout(function() { copyBtn.textContent = 'Copy All Logs'; copyBtn.style.background = '#e85d04'; }, 1500);
        }).catch(function() {
            // Fallback: create a textarea for manual copy
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;top:10%;left:5%;width:90%;height:40%;z-index:999999;font-size:12px;font-family:monospace;background:#111;color:#0f0;padding:8px;border:2px solid #e85d04;';
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'Close (select all + copy first)';
            closeBtn.style.cssText = 'position:fixed;top:calc(10% - 30px);left:5%;z-index:999999;background:#e85d04;color:#fff;border:none;padding:6px 16px;cursor:pointer;font-weight:bold;';
            closeBtn.addEventListener('click', function() { ta.remove(); closeBtn.remove(); });
            document.body.appendChild(closeBtn);
            document.body.appendChild(ta);
            ta.select();
        });
    });

    // Clear button
    const clearBtn = document.createElement('button');
    clearBtn.textContent = 'Clear';
    clearBtn.style.cssText = 'background:#555;color:#fff;border:none;padding:4px 10px;border-radius:4px;' +
        'cursor:pointer;font-family:monospace;font-size:12px;';
    clearBtn.addEventListener('click', function() {
        const logArea = document.getElementById('neon-debug-logs');
        if (logArea) logArea.innerHTML = '';
        _debugLogs.length = 0;
    });

    btnGroup.appendChild(copyBtn);
    btnGroup.appendChild(clearBtn);
    toolbar.appendChild(title);
    toolbar.appendChild(btnGroup);
    panel.appendChild(toolbar);

    // Log area
    const logArea = document.createElement('div');
    logArea.id = 'neon-debug-logs';
    panel.appendChild(logArea);

    document.body.appendChild(panel);
    return panel;
}

function debugLog(label, data) {
    const ts = new Date().toISOString().slice(11, 23);
    const entry = `[${ts}] ${label}: ${typeof data === 'string' ? data : JSON.stringify(data, null, 2)}`;
    _debugLogs.push(entry);
    console.log(`%c[NeonAuth] ${label}`, 'color:#e85d04;font-weight:bold', data);

    const panel = _createDebugPanel();
    const logArea = document.getElementById('neon-debug-logs');
    if (logArea) {
        const line = document.createElement('div');
        line.style.cssText = 'border-bottom:1px solid #333;padding:2px 0;';
        line.textContent = entry;
        logArea.appendChild(line);
    }
    panel.scrollTop = panel.scrollHeight;
}
// ======================================

class NeonAuthClient {
    constructor(authUrl) {
        this.authUrl = authUrl.replace(/\/$/, '');
        debugLog('INIT', { authUrl: this.authUrl, origin: window.location.origin, href: window.location.href });
    }

    async signInWithGoogle() {
        const callbackUrl = `${window.location.origin}/auth/callback`;
        debugLog('signInWithGoogle', { callbackUrl });

        try {
            const response = await fetch(`${this.authUrl}/sign-in/social`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: 'google', callbackURL: callbackUrl }),
                credentials: 'include'
            });

            debugLog('signInWithGoogle response', { status: response.status, ok: response.ok });
            const data = await response.json();
            debugLog('signInWithGoogle data', data);

            if (response.ok && data.url) {
                debugLog('signInWithGoogle redirect', data.url);
                window.location.href = data.url;
                return;
            }

            throw new Error('Failed to initiate Google sign-in');
        } catch (error) {
            debugLog('signInWithGoogle ERROR', error.message);
            throw error;
        }
    }

    async signUp(email, password, name = '') {
        try {
            const response = await fetch(`${this.authUrl}/sign-up/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name }),
                credentials: 'include'
            });

            const data = await response.json();
            debugLog('signUp response', { status: response.status, data });

            if (!response.ok) {
                throw new Error(data.message || 'Sign up failed');
            }

            return { success: true, data: data };
        } catch (error) {
            debugLog('signUp ERROR', error.message);
            throw error;
        }
    }

    async verifyEmail(email, otp) {
        try {
            const response = await fetch(`${this.authUrl}/email-otp/verify-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp }),
                credentials: 'include'
            });

            const data = await response.json();
            debugLog('verifyEmail response', { status: response.status, dataKeys: Object.keys(data), data });

            if (!response.ok) {
                throw new Error(data.message || 'Verification failed');
            }

            const token = (data.session && data.session.token) || data.token || null;
            debugLog('verifyEmail token extracted', { hasToken: !!token, tokenPrefix: token ? token.substring(0, 20) + '...' : null });
            return { success: true, token: token };
        } catch (error) {
            debugLog('verifyEmail ERROR', error.message);
            throw error;
        }
    }

    async resendOtp(email, type = 'email-verification') {
        try {
            const response = await fetch(`${this.authUrl}/email-otp/send-verification-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, type }),
                credentials: 'include'
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Failed to resend code');
            }
            return { success: true };
        } catch (error) {
            debugLog('resendOtp ERROR', error.message);
            throw error;
        }
    }

    async signInWithEmailPassword(email, password) {
        debugLog('signInWithEmailPassword START', { email });

        try {
            // Step 1: Call Neon Auth sign-in
            const response = await fetch(`${this.authUrl}/sign-in/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
                credentials: 'include'
            });

            const data = await response.json();
            debugLog('signIn Neon response', {
                status: response.status,
                ok: response.ok,
                dataKeys: Object.keys(data),
                hasSession: !!data.session,
                hasToken: !!data.token,
                hasUser: !!data.user,
                sessionKeys: data.session ? Object.keys(data.session) : null,
                fullData: data
            });

            if (!response.ok) {
                throw new Error(data.message || 'Sign in failed');
            }

            // Step 2: Extract token
            const token = (data.session && data.session.token) || data.token || null;
            debugLog('signIn token extracted', {
                hasToken: !!token,
                tokenLength: token ? token.length : 0,
                tokenPrefix: token ? token.substring(0, 30) + '...' : null
            });

            // Step 3: Also pass user data from the sign-in response
            const callbackPayload = {};
            if (token) {
                callbackPayload.token = token;
            }
            if (data.user) {
                callbackPayload.user = data.user;
            }
            debugLog('signIn calling /auth/neon-callback', { payloadKeys: Object.keys(callbackPayload), hasToken: !!callbackPayload.token, hasUser: !!callbackPayload.user });

            const callbackResponse = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(callbackPayload),
                credentials: 'include'
            });

            const callbackText = await callbackResponse.text();
            debugLog('signIn callback response', {
                status: callbackResponse.status,
                ok: callbackResponse.ok,
                body: callbackText
            });

            if (callbackResponse.ok) {
                const callbackData = JSON.parse(callbackText);
                return { success: true, redirect: callbackData.redirect || '/dashboard' };
            }

            // Step 4: Retry with getSession (includes full user data)
            debugLog('signIn callback failed, trying getSession fallback', {});
            const fullSession = await this._getFullSession();
            debugLog('signIn getFullSession result', fullSession);

            if (fullSession && fullSession.user) {
                const sessionToken = fullSession.session ? fullSession.session.token : null;
                const retryPayload = { user: fullSession.user };
                if (sessionToken) {
                    retryPayload.token = sessionToken;
                }

                debugLog('signIn retry with user data', { hasToken: !!sessionToken, userId: fullSession.user.id });

                const retryResponse = await fetch('/auth/neon-callback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(retryPayload),
                    credentials: 'include'
                });

                const retryText = await retryResponse.text();
                debugLog('signIn retry callback response', {
                    status: retryResponse.status,
                    ok: retryResponse.ok,
                    body: retryText
                });

                if (retryResponse.ok) {
                    const retryData = JSON.parse(retryText);
                    return { success: true, redirect: retryData.redirect || '/dashboard' };
                }
            }

            throw new Error('Failed to establish session');
        } catch (error) {
            debugLog('signInWithEmailPassword FINAL ERROR', error.message);
            throw error;
        }
    }

    /**
     * Get current Neon Auth session object (session field only)
     */
    async getSession() {
        debugLog('getSession START', { url: `${this.authUrl}/get-session` });
        try {
            const response = await fetch(`${this.authUrl}/get-session`, {
                method: 'GET',
                credentials: 'include'
            });

            debugLog('getSession response', { status: response.status, ok: response.ok });

            if (!response.ok) {
                debugLog('getSession NOT OK', { status: response.status });
                return null;
            }

            const data = await response.json();
            debugLog('getSession data', {
                dataKeys: Object.keys(data),
                hasSession: !!data.session,
                hasUser: !!data.user,
                hasToken: !!data.token,
                sessionKeys: data.session ? Object.keys(data.session) : null,
                userKeys: data.user ? Object.keys(data.user) : null,
                fullData: data
            });

            if (data.session) {
                return data.session;
            }
            if (data.token) {
                return data;
            }
            return null;
        } catch (error) {
            debugLog('getSession ERROR', error.message);
            return null;
        }
    }

    /**
     * Get full session data including user object from Neon Auth
     * Returns { session: {...}, user: {...} } or null
     */
    async _getFullSession() {
        try {
            const response = await fetch(`${this.authUrl}/get-session`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) return null;

            const data = await response.json();
            if (data.session && data.user) {
                return { session: data.session, user: data.user };
            }
            return null;
        } catch (error) {
            debugLog('_getFullSession ERROR', error.message);
            return null;
        }
    }

    async signOut() {
        try {
            await fetch(`${this.authUrl}/sign-out`, {
                method: 'POST',
                credentials: 'include'
            });
            return { success: true };
        } catch (error) {
            debugLog('signOut ERROR', error.message);
            throw error;
        }
    }

    async handleCallback() {
        debugLog('handleCallback START', {});
        try {
            const sessionData = await this.getSession();
            const token = sessionData ? (sessionData.token || null) : null;
            debugLog('handleCallback session', { hasSession: !!sessionData, hasToken: !!token });

            const payload = {};
            if (token) {
                payload.token = token;
            }

            const response = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            });

            const text = await response.text();
            debugLog('handleCallback response', { status: response.status, ok: response.ok, body: text });

            if (response.ok) {
                const data = JSON.parse(text);
                return { success: true, redirect: data.redirect || '/dashboard' };
            }
        } catch (error) {
            debugLog('handleCallback ERROR', error.message);
        }

        return { success: false };
    }

    async checkSessionVerifier() {
        const params = new URLSearchParams(window.location.search);
        const verifier = params.get('neon_auth_session_verifier');

        if (!verifier) return false;

        debugLog('checkSessionVerifier DETECTED', { verifier, fullUrl: window.location.href });

        try {
            // Don't clean URL yet — keep it visible for debugging
            // const cleanUrl = window.location.pathname || '/';
            // window.history.replaceState({}, '', cleanUrl);

            // Step 1: Get full session from Neon Auth (includes user data)
            debugLog('checkSessionVerifier calling getFullSession', {});
            const fullSession = await this._getFullSession();
            const token = fullSession && fullSession.session ? fullSession.session.token : null;
            const userData = fullSession ? fullSession.user : null;
            debugLog('checkSessionVerifier session result', {
                hasSession: !!fullSession,
                hasToken: !!token,
                hasUser: !!userData,
                tokenPrefix: token ? token.substring(0, 30) + '...' : null,
                userId: userData ? userData.id : null,
                userEmail: userData ? userData.email : null
            });

            // Step 2: POST to Flask with token + user data
            const payload = {};
            if (token) {
                payload.token = token;
            }
            if (userData) {
                payload.user = userData;
            }

            debugLog('checkSessionVerifier calling /auth/neon-callback', { payloadKeys: Object.keys(payload), hasToken: !!payload.token, hasUser: !!payload.user });
            const response = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                credentials: 'include'
            });

            const text = await response.text();
            debugLog('checkSessionVerifier callback response', {
                status: response.status,
                ok: response.ok,
                body: text
            });

            if (response.ok) {
                const data = JSON.parse(text);
                debugLog('checkSessionVerifier SUCCESS, redirecting', data.redirect || '/dashboard');
                window.location.href = data.redirect || '/dashboard';
                return true;
            }

            debugLog('checkSessionVerifier ALL ATTEMPTS FAILED', 'Staying on page for debug inspection');
            // Don't redirect to login — stay on page so user can copy debug logs
            return false;
        } catch (error) {
            debugLog('checkSessionVerifier ERROR', error.message);
            return false;
        }
    }
}

// Initialize Neon Auth client when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const authUrlMeta = document.querySelector('meta[name="neon-auth-url"]');
    const authUrl = authUrlMeta ? authUrlMeta.content : null;

    debugLog('DOMContentLoaded', {
        hasAuthUrlMeta: !!authUrlMeta,
        authUrl: authUrl,
        currentUrl: window.location.href,
        cookies: document.cookie || '(none visible to JS)'
    });

    if (authUrl) {
        window.neonAuth = new NeonAuthClient(authUrl);
        window.neonAuth.checkSessionVerifier();
    } else {
        debugLog('WARN', 'No neon-auth-url meta tag found — NeonAuthClient NOT initialized');
    }
});
