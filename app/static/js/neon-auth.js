/**
 * Neon Auth Client Integration
 * Handles OAuth and email-based authentication with Neon Auth (Better Auth)
 */

class NeonAuthClient {
    constructor(authUrl) {
        this.authUrl = authUrl.replace(/\/$/, ''); // Remove trailing slash
        this.sessionKey = 'neon_auth_session';
    }

    /**
     * Sign in with Google OAuth
     */
    async signInWithGoogle() {
        const callbackUrl = `${window.location.origin}/auth/callback`;
        const authUrl = `${this.authUrl}/sign-in/social?provider=google&callbackURL=${encodeURIComponent(callbackUrl)}`;
        window.location.href = authUrl;
    }

    /**
     * Sign in with email (magic link)
     */
    async signInWithEmail(email) {
        try {
            const response = await fetch(`${this.authUrl}/sign-in/magic-link`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    callbackURL: `${window.location.origin}/auth/callback`
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to send magic link');
            }

            return { success: true, message: 'Check your email for the sign-in link' };
        } catch (error) {
            console.error('Magic link error:', error);
            throw error;
        }
    }

    /**
     * Sign up with email and password
     */
    async signUp(email, password, name = '') {
        try {
            const response = await fetch(`${this.authUrl}/sign-up/email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    name: name,
                    callbackURL: `${window.location.origin}/auth/callback`
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Sign up failed');
            }

            const data = await response.json();
            return { success: true, user: data.user, session: data.session };
        } catch (error) {
            console.error('Sign up error:', error);
            throw error;
        }
    }

    /**
     * Sign in with email and password
     */
    async signInWithEmailPassword(email, password) {
        try {
            const response = await fetch(`${this.authUrl}/sign-in/email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                }),
                credentials: 'include'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Sign in failed');
            }

            const data = await response.json();
            
            // Store session token
            if (data.session && data.session.token) {
                this.setSession(data.session.token);
            }

            return { success: true, user: data.user, session: data.session };
        } catch (error) {
            console.error('Sign in error:', error);
            throw error;
        }
    }

    /**
     * Get current session
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
            return data.session;
        } catch (error) {
            console.error('Get session error:', error);
            return null;
        }
    }

    /**
     * Sign out
     */
    async signOut() {
        try {
            await fetch(`${this.authUrl}/sign-out`, {
                method: 'POST',
                credentials: 'include'
            });
            
            this.clearSession();
            return { success: true };
        } catch (error) {
            console.error('Sign out error:', error);
            this.clearSession();
            throw error;
        }
    }

    /**
     * Store session token locally
     */
    setSession(token) {
        localStorage.setItem(this.sessionKey, token);
    }

    /**
     * Get stored session token
     */
    getStoredSession() {
        return localStorage.getItem(this.sessionKey);
    }

    /**
     * Clear stored session
     */
    clearSession() {
        localStorage.removeItem(this.sessionKey);
    }

    /**
     * Check if user is authenticated
     */
    async isAuthenticated() {
        const session = await this.getSession();
        return session !== null;
    }

    /**
     * Handle OAuth callback
     */
    async handleCallback() {
        // The session should be set via cookies from the OAuth flow
        const session = await this.getSession();
        
        if (session) {
            // Notify the backend about the successful authentication
            try {
                const response = await fetch('/auth/neon-callback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include'
                });

                if (response.ok) {
                    const data = await response.json();
                    return { success: true, redirect: data.redirect || '/dashboard' };
                }
            } catch (error) {
                console.error('Callback handling error:', error);
            }
        }

        return { success: false };
    }
}

// Initialize Neon Auth client when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Get Neon Auth URL from meta tag or config
    const authUrlMeta = document.querySelector('meta[name="neon-auth-url"]');
    const authUrl = authUrlMeta ? authUrlMeta.content : null;

    if (authUrl) {
        window.neonAuth = new NeonAuthClient(authUrl);
        console.log('Neon Auth client initialized');
    }
});
