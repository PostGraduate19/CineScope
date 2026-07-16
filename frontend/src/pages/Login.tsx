import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, UserPlus, Users } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

export function Login() {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [guestName, setGuestName] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login, continueAsGuest } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            const endpoint = isLogin ? '/auth/login' : '/auth/register';
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Authentication failed');
            }

            if (isLogin) {
                login(data.token, data.username);
                navigate('/');
            } else {
                setIsLogin(true);
                setError('Registration successful! Please login.');
            }
        } catch (err: any) {
            setError(err.message);
        }
    };

    const handleGuest = (e: React.FormEvent) => {
        e.preventDefault();
        if (guestName.trim()) {
            continueAsGuest(guestName.trim());
            navigate('/');
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
                <div className="p-8">
                    <h2 className="text-3xl font-bold text-white text-center mb-8">
                        {isLogin ? 'Welcome Back' : 'Create Account'}
                    </h2>
                    
                    {error && (
                        <div className="bg-red-500/10 border border-red-500 text-red-500 rounded p-3 mb-6 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            className="w-full flex items-center justify-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            {isLogin ? (
                                <><LogIn className="w-5 h-5 mr-2" /> Login</>
                            ) : (
                                <><UserPlus className="w-5 h-5 mr-2" /> Register</>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-sm text-blue-400 hover:text-blue-300"
                        >
                            {isLogin ? 'Need an account? Register' : 'Already have an account? Login'}
                        </button>
                    </div>

                    <div className="mt-8 pt-8 border-t border-gray-700">
                        <p className="text-sm text-gray-400 text-center mb-4">Or continue without an account</p>
                        <form onSubmit={handleGuest} className="space-y-4">
                            <input
                                type="text"
                                placeholder="Guest Display Name"
                                value={guestName}
                                onChange={(e) => setGuestName(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-gray-500"
                                required
                            />
                            <button
                                type="submit"
                                className="w-full flex items-center justify-center py-2.5 px-4 border border-gray-600 rounded-lg shadow-sm text-sm font-medium text-white bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                            >
                                <Users className="w-5 h-5 mr-2" /> Continue as Guest
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
