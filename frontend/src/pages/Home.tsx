import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Video, LogOut } from 'lucide-react';

export function Home() {
    const [roomId, setRoomId] = useState('');
    const navigate = useNavigate();
    const { username, logout } = useAuth();

    const generateRoom = () => {
        const id = Math.random().toString(36).substring(2, 9);
        navigate(`/room/${id}`);
    };

    const joinRoom = (e: React.FormEvent) => {
        e.preventDefault();
        if (roomId.trim()) {
            navigate(`/room/${roomId}`);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
            <div className="absolute top-4 right-4 flex items-center gap-4">
                <span className="text-gray-300">Logged in as: <strong className="text-white">{username}</strong></span>
                <button
                    onClick={() => {
                        logout();
                        navigate('/login');
                    }}
                    className="flex items-center text-red-400 hover:text-red-300"
                >
                    <LogOut className="w-5 h-5 mr-1" /> Logout
                </button>
            </div>

            <div className="max-w-md w-full bg-gray-800 rounded-xl shadow-2xl p-8 text-center">
                <Video className="w-16 h-16 text-blue-500 mx-auto mb-6" />
                <h1 className="text-4xl font-bold text-white mb-2">Watch Party</h1>
                <p className="text-gray-400 mb-8">Watch videos in perfect sync with friends.</p>

                <button
                    onClick={generateRoom}
                    className="w-full mb-6 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
                >
                    Create New Room
                </button>

                <div className="relative mb-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-700"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-gray-800 text-gray-400">Or join existing</span>
                    </div>
                </div>

                <form onSubmit={joinRoom} className="flex gap-2">
                    <input
                        type="text"
                        placeholder="Enter Room ID"
                        value={roomId}
                        onChange={(e) => setRoomId(e.target.value)}
                        className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                        required
                    />
                    <button
                        type="submit"
                        className="py-3 px-6 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
                    >
                        Join
                    </button>
                </form>
            </div>
        </div>
    );
}
