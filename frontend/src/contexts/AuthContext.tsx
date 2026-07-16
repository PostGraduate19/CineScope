import React, { createContext, useContext, useState } from 'react';

interface AuthContextType {
    token: string | null;
    username: string | null;
    login: (token: string, username: string) => void;
    logout: () => void;
    continueAsGuest: (guestName: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [username, setUsername] = useState<string | null>(localStorage.getItem('username'));

    const login = (newToken: string, newUsername: string) => {
        setToken(newToken);
        setUsername(newUsername);
        localStorage.setItem('token', newToken);
        localStorage.setItem('username', newUsername);
    };

    const logout = () => {
        setToken(null);
        setUsername(null);
        localStorage.removeItem('token');
        localStorage.removeItem('username');
    };

    const continueAsGuest = (guestName: string) => {
        setUsername(guestName);
        localStorage.setItem('username', guestName);
    };

    return (
        <AuthContext.Provider value={{ token, username, login, logout, continueAsGuest }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
