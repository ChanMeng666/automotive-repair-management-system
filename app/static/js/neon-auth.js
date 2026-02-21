/**
 * Neon Auth Client Integration
 * Handles email+password and Google OAuth authentication via Neon Auth (Better Auth)
 */

class NeonAuthClient {
    constructor(authUrl) {
        this.authUrl = authUrl.replace(/\/$/, '');
    }

    /**
     * Sign in with Google OAuth via Better Auth social sign-in
     */
    async signInWithGoogle() {
        const callbackUrl = `${window.location.origin}/auth/callback`;

        try {
            const response = await fetch(`${this.authUrl}/sign-in/social`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: 'google',
                    callbackURL: callbackUrl
                }),
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.url) {
                    window.location.href = data.url;
                    return;
                }
            }

            throw new Error('Failed to initiate Google sign-in');
        } catch (error) {
            console.error('Google sign-in error:', error);
            throw error;
        }
    }

    /**
     * Sign up with email and password
     * Returns response for UI to show verification step (does NOT auto-establish session)
     */
    async signUp(email, password, name = '') {
        try {
            const response = await fetch(`${this.authUrl}/sign-up/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    name: name
                }),
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Sign up failed');
            }

            // Return data - UI will show verification code input
            return { success: true, data: data };
        } catch (error) {
            console.error('Sign up error:', error);
            throw error;
        }
    }

    /**
     * Verify email with OTP code
     * Returns the session token from the response so callers can pass it to Flask
     */
    async verifyEmail(email, otp) {
        try {
            const response = await fetch(`${this.authUrl}/email-otp/verify-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp }),
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Verification failed');
            }

            // Extract session token from response
            const token = (data.session && data.session.token) || data.token || null;
            return { success: true, token: token };
        } catch (error) {
            console.error('Email verification error:', error);
            throw error;
        }
    }

    /**
     * Resend OTP verification code
     */
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
            console.error('Resend OTP error:', error);
            throw error;
        }
    }

    /**
     * Sign in with email and password
     * On success, establishes Flask session via /auth/neon-callback
     */
    async signInWithEmailPassword(email, password) {
        try {
            const response = await fetch(`${this.authUrl}/sign-in/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Sign in failed');
            }

            // Extract token from Neon Auth response
            const token = (data.session && data.session.token) || data.token || null;

            // Establish Flask session - pass token in body since cookie may not be visible cross-origin
            const callbackPayload = {};
            if (token) {
                callbackPayload.token = token;
            }

            const callbackResponse = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(callbackPayload),
                credentials: 'include'
            });

            if (callbackResponse.ok) {
                const callbackData = await callbackResponse.json();
                return {
                    success: true,
                    redirect: callbackData.redirect || '/dashboard'
                };
            }

            // If the token from sign-in response didn't work,
            // try fetching a fresh session from Neon Auth
            const sessionData = await this.getSession();
            if (sessionData) {
                const sessionToken = sessionData.token || null;
                const retryPayload = {};
                if (sessionToken) {
                    retryPayload.token = sessionToken;
                }

                const retryResponse = await fetch('/auth/neon-callback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(retryPayload),
                    credentials: 'include'
                });

                if (retryResponse.ok) {
                    const retryData = await retryResponse.json();
                    return {
                        success: true,
                        redirect: retryData.redirect || '/dashboard'
                    };
                }
            }

            throw new Error('Failed to establish session');
        } catch (error) {
            console.error('Sign in error:', error);
            throw error;
        }
    }

    /**
     * Get current Neon Auth session
     */
    async getSession() {
        try {
            const response = await fetch(`${this.authUrl}/get-session`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                return null;
            }

            const data = await response.json();
            // Better Auth may return { session: {...}, user: {...} } or { session: null }
            if (data.session) {
                return data.session;
            }
            // Some responses nest differently
            if (data.token) {
                return data;
            }
            return null;
        } catch (error) {
            console.error('Get session error:', error);
            return null;
        }
    }

    /**
     * Sign out from Neon Auth
     */
    async signOut() {
        try {
            await fetch(`${this.authUrl}/sign-out`, {
                method: 'POST',
                credentials: 'include'
            });
            return { success: true };
        } catch (error) {
            console.error('Sign out error:', error);
            throw error;
        }
    }

    /**
     * Handle OAuth callback - get session from Neon Auth and pass token to Flask
     */
    async handleCallback() {
        try {
            // Get session from Neon Auth (client-side cookie is visible to Neon Auth domain)
            const sessionData = await this.getSession();
            const token = sessionData ? (sessionData.token || null) : null;

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

            if (response.ok) {
                const data = await response.json();
                return { success: true, redirect: data.redirect || '/dashboard' };
            }
        } catch (error) {
            console.error('Callback handling error:', error);
        }

        return { success: false };
    }

    /**
     * Check for neon_auth_session_verifier in URL and complete the auth flow.
     * Called automatically on every page load. After Google OAuth, Neon Auth
     * redirects to the app's origin with ?neon_auth_session_verifier=... param.
     * This method detects that, gets the session, and establishes a Flask session.
     */
    async checkSessionVerifier() {
        const params = new URLSearchParams(window.location.search);
        const verifier = params.get('neon_auth_session_verifier');

        if (!verifier) return false;

        try {
            // Clean the URL immediately to prevent re-triggering
            const cleanUrl = window.location.pathname || '/';
            window.history.replaceState({}, '', cleanUrl);

            // Get session from Neon Auth — the session cookie should be set after OAuth
            const sessionData = await this.getSession();
            const token = sessionData ? (sessionData.token || null) : null;

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

            if (response.ok) {
                const data = await response.json();
                window.location.href = data.redirect || '/dashboard';
                return true;
            }

            // If getSession didn't return a token, try using the verifier directly
            // as a token (some Better Auth configurations return it this way)
            if (!token) {
                const verifierResponse = await fetch('/auth/neon-callback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: verifier }),
                    credentials: 'include'
                });

                if (verifierResponse.ok) {
                    const data = await verifierResponse.json();
                    window.location.href = data.redirect || '/dashboard';
                    return true;
                }
            }

            console.warn('Session verifier detected but could not establish session');
            window.location.href = '/auth/login';
            return false;
        } catch (error) {
            console.error('Session verifier handling error:', error);
            window.location.href = '/auth/login';
            return false;
        }
    }
}

// Initialize Neon Auth client when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const authUrlMeta = document.querySelector('meta[name="neon-auth-url"]');
    const authUrl = authUrlMeta ? authUrlMeta.content : null;

    if (authUrl) {
        window.neonAuth = new NeonAuthClient(authUrl);

        // Auto-detect OAuth redirect with session verifier
        window.neonAuth.checkSessionVerifier();
    }
});
