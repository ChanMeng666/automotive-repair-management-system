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

            return { success: true };
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

            // Establish Flask session
            const callbackResponse = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });

            if (callbackResponse.ok) {
                const callbackData = await callbackResponse.json();
                return {
                    success: true,
                    redirect: callbackData.redirect || '/dashboard'
                };
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
            return data.session;
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
     * Handle OAuth callback - establish Flask session after redirect
     */
    async handleCallback() {
        try {
            const response = await fetch('/auth/neon-callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
}

// Initialize Neon Auth client when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const authUrlMeta = document.querySelector('meta[name="neon-auth-url"]');
    const authUrl = authUrlMeta ? authUrlMeta.content : null;

    if (authUrl) {
        window.neonAuth = new NeonAuthClient(authUrl);
    }
});
