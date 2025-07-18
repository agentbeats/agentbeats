import { writable, derived } from 'svelte/store';
import type { User, AuthError } from '@supabase/supabase-js';
import { supabase, user, loading, error } from '$lib/auth/supabase';

// Derived stores
export const isAuthenticated = derived(user, ($user) => !!$user);
export const userEmail = derived(user, ($user) => $user?.email);
export const userName = derived(user, ($user) => $user?.user_metadata?.name || $user?.email);
export const userId = derived(user, ($user) => $user?.id);

// Re-export the stores from supabase client
export { user, loading, error };

// Auth functions following Supabase best practices
export const setUser = (newUser: User | null) => {
	user.set(newUser);
	loading.set(false);
	error.set(null);
};

export const setLoading = (isLoading: boolean) => {
	loading.set(isLoading);
};

export const setError = (authError: AuthError | null) => {
	error.set(authError);
};

export const clearAuth = () => {
	user.set(null);
	loading.set(false);
	error.set(null);
	// Clear local storage safely
	if (typeof window !== 'undefined') {
		localStorage.removeItem('auth_token');
		localStorage.removeItem('user_id');
	}
};

// User management functions following Supabase patterns
export const getUser = async (): Promise<User | null> => {
	try {
		const { data: { user: currentUser }, error: userError } = await supabase.auth.getUser();
		
		if (userError) {
			console.error('Error getting user:', userError);
			error.set(userError);
			return null;
		}
		
		return currentUser;
	} catch (err) {
		console.error('Get user error:', err);
		error.set(err as AuthError);
		return null;
	}
};

export const updateUser = async (updates: {
	email?: string;
	password?: string;
	data?: Record<string, any>;
}): Promise<User | null> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { data: { user: updatedUser }, error: updateError } = await supabase.auth.updateUser(updates);
		
		if (updateError) {
			console.error('Error updating user:', updateError);
			error.set(updateError);
			return null;
		}
		
		// Update the store with the new user data
		user.set(updatedUser);
		return updatedUser;
	} catch (err) {
		console.error('Update user error:', err);
		error.set(err as AuthError);
		return null;
	} finally {
		loading.set(false);
	}
};

export const resetPassword = async (email: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { error: resetError } = await supabase.auth.resetPasswordForEmail(email);
		
		if (resetError) {
			console.error('Error resetting password:', resetError);
			error.set(resetError);
			return false;
		}
		
		return true;
	} catch (err) {
		console.error('Reset password error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

// Email/Password authentication functions
export const signUpWithEmail = async (email: string, password: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { data, error: signUpError } = await supabase.auth.signUp({
			email,
			password
		});
		
		if (signUpError) {
			console.error('Error signing up:', signUpError);
			error.set(signUpError);
			return false;
		}
		
		// If email confirmation is required, data.user will be null
		if (data.user) {
			user.set(data.user);
		}
		
		return true;
	} catch (err) {
		console.error('Sign up error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

export const signInWithEmail = async (email: string, password: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { data, error: signInError } = await supabase.auth.signInWithPassword({
			email,
			password
		});
		
		if (signInError) {
			console.error('Error signing in:', signInError);
			error.set(signInError);
			return false;
		}
		
		user.set(data.user);
		return true;
	} catch (err) {
		console.error('Sign in error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

export const signInWithMagicLink = async (email: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { error: magicLinkError } = await supabase.auth.signInWithOtp({
			email
		});
		
		if (magicLinkError) {
			console.error('Error sending magic link:', magicLinkError);
			error.set(magicLinkError);
			return false;
		}
		
		return true;
	} catch (err) {
		console.error('Magic link error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

// Phone authentication functions (if you want to support SMS)
export const signUpWithPhone = async (phone: string, password: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { data, error: signUpError } = await supabase.auth.signUp({
			phone,
			password
		});
		
		if (signUpError) {
			console.error('Error signing up with phone:', signUpError);
			error.set(signUpError);
			return false;
		}
		
		if (data.user) {
			user.set(data.user);
		}
		
		return true;
	} catch (err) {
		console.error('Phone sign up error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

export const signInWithPhoneOtp = async (phone: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { error: otpError } = await supabase.auth.signInWithOtp({
			phone
		});
		
		if (otpError) {
			console.error('Error sending phone OTP:', otpError);
			error.set(otpError);
			return false;
		}
		
		return true;
	} catch (err) {
		console.error('Phone OTP error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
};

export const verifyPhoneOtp = async (phone: string, token: string): Promise<boolean> => {
	try {
		loading.set(true);
		error.set(null);
		
		const { data, error: verifyError } = await supabase.auth.verifyOtp({
			phone,
			token,
			type: 'sms'
		});
		
		if (verifyError) {
			console.error('Error verifying phone OTP:', verifyError);
			error.set(verifyError);
			return false;
		}
		
		if (data.user) {
			user.set(data.user);
		}
		
		return true;
	} catch (err) {
		console.error('Phone OTP verification error:', err);
		error.set(err as AuthError);
		return false;
	} finally {
		loading.set(false);
	}
}; 