/**
 * Neon Auth Client Integration
 * Handles email+password and Google OAuth authentication via Neon Auth (Better Auth)
 */

class NeonAuthClient {
    constructor(authUrl) {
        this.authUrl = authUrl.replace(/\/$/, '');
    }

    async signInWithGoogle() {
        const callbackUrl = `${window.location.origin}/auth/callback`;

        const response = await fetch(`${this.authUrl}/sign-in/social`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: 'google', callbackURL: callbackUrl }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok && data.url) {
            window.location.href = data.url;
            return;
        }

        throw new Error('Failed to initiate Google sign-in');
    }

    async signUp(email, password, name = '') {
        const response = await fetch(`${this.authUrl}/sign-up/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name }),
            credentials: 'include'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Sign up failed');
        }

        return { success: true, data: data };
    }

    async verifyEmail(email, otp) {
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

        const token = (data.session && data.session.token) || data.token || null;
        return { success: true, token: token };
    }

    async resendOtp(email, type = 'email-verification') {
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
    }

    async signInWithEmailPassword(email, password) {
        // Step 1: Call Neon Auth sign-in
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

        // Step 2: Extract token and user data
        const token = (data.session && data.session.token) || data.token || null;
        const callbackPayload = {};
        if (token) callbackPayload.token = token;
        if (data.user) callbackPayload.user = data.user;

        // Step 3: Notify Flask backend
        const callbackResponse = await fetch('/auth/neon-callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(callbackPayload),
            credentials: 'include'
        });

        if (callbackResponse.ok) {
            const callbackData = await callbackResponse.json();
            return { success: true, redirect: callbackData.redirect || '/dashboard' };
        }

        // Step 4: Retry with full session from Neon Auth
        const fullSession = await this._getFullSession();

        if (fullSession && fullSession.user) {
            const sessionToken = fullSession.session ? fullSession.session.token : null;
            const retryPayload = { user: fullSession.user };
            if (sessionToken) retryPayload.token = sessionToken;

            const retryResponse = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(retryPayload),
                credentials: 'include'
            });

            if (retryResponse.ok) {
                const retryData = await retryResponse.json();
                return { success: true, redirect: retryData.redirect || '/dashboard' };
            }
        }

        throw new Error('Failed to establish session');
    }

    /**
     * Get current Neon Auth session object (session field only)
     */
    async getSession() {
        try {
            const response = await fetch(`${this.authUrl}/get-session`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) return null;

            const data = await response.json();

            if (data && data.session) return data.session;
            if (data && data.token) return data;
            return null;
        } catch (error) {
            console.error('getSession error:', error);
            return null;
        }
    }

    /**
     * Get full session data including user object from Neon Auth
     */
    async _getFullSession() {
        try {
            const response = await fetch(`${this.authUrl}/get-session`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) return null;

            const data = await response.json();
            if (data && data.session && data.user) {
                return { session: data.session, user: data.user };
            }
            return null;
        } catch (error) {
            console.error('_getFullSession error:', error);
            return null;
        }
    }

    async signOut() {
        await fetch(`${this.authUrl}/sign-out`, {
            method: 'POST',
            credentials: 'include'
        });
        return { success: true };
    }

    async handleCallback() {
        try {
            const sessionData = await this.getSession();
            const token = sessionData ? (sessionData.token || null) : null;

            const payload = {};
            if (token) payload.token = token;

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
            console.error('handleCallback error:', error);
        }

        return { success: false };
    }

    async checkSessionVerifier() {
        const params = new URLSearchParams(window.location.search);
        const verifier = params.get('neon_auth_session_verifier');

        if (!verifier) return false;

        try {
            // Clean the URL to remove the verifier param
            const cleanUrl = window.location.pathname || '/';
            window.history.replaceState({}, '', cleanUrl);

            // Get full session from Neon Auth (includes user data)
            const fullSession = await this._getFullSession();
            const token = fullSession && fullSession.session ? fullSession.session.token : null;
            const userData = fullSession ? fullSession.user : null;

            // POST to Flask with token + user data
            const payload = {};
            if (token) payload.token = token;
            if (userData) payload.user = userData;

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

            return false;
        } catch (error) {
            console.error('checkSessionVerifier error:', error);
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
        window.neonAuth.checkSessionVerifier();
    }
});
