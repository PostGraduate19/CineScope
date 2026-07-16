import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io, Socket } from 'socket.io-client';
// @ts-ignore
import ReactPlayer from 'react-player';
import { useAuth } from '../contexts/AuthContext';
import { Users, Link, FileVideo, Copy, ArrowLeft } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

interface User {
    id: string;
    username: string;
}

export function Room() {
    const { id } = useParams<{ id: string }>();
    const { token, username } = useAuth();
    const navigate = useNavigate();
    
    const [socket, setSocket] = useState<Socket | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [urlInput, setUrlInput] = useState('');
    const [currentUrl, setCurrentUrl] = useState<string | null>(null);
    const [localFileUrl, setLocalFileUrl] = useState<string | null>(null);
    
    const playerRef = useRef<any>(null);
    const nativePlayerRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const isSeekingRef = useRef(false);

    useEffect(() => {
        if (!username) {
            navigate('/login');
            return;
        }

        const newSocket = io(API_URL, {
            auth: { token }
        });

        setSocket(newSocket);

        newSocket.on('connect', () => {
            newSocket.emit('join-room', id);
        });

        newSocket.on('room-state', (state) => {
            if (state.url) {
                setCurrentUrl(state.url);
                setLocalFileUrl(null);
            }
            setIsPlaying(state.playing);
            
            // Wait for player to be ready before seeking for late joiners
            setTimeout(() => {
                if (playerRef.current && state.url) {
                    playerRef.current.seekTo(state.time, 'seconds');
                } else if (nativePlayerRef.current) {
                    nativePlayerRef.current.currentTime = state.time;
                    if (state.playing) {
                        nativePlayerRef.current.play().catch(console.error);
                    }
                }
            }, 500);
        });

        newSocket.on('users-update', (updatedUsers) => {
            setUsers(updatedUsers);
        });

        newSocket.on('play', (time) => {
            isSeekingRef.current = true;
            if (playerRef.current && currentUrl) playerRef.current.seekTo(time, 'seconds');
            if (nativePlayerRef.current) {
                nativePlayerRef.current.currentTime = time;
                nativePlayerRef.current.play().catch(console.error);
            }
            setIsPlaying(true);
            setTimeout(() => { isSeekingRef.current = false; }, 500);
        });

        newSocket.on('pause', (time) => {
            setIsPlaying(false);
            if (playerRef.current && currentUrl) playerRef.current.seekTo(time, 'seconds');
            if (nativePlayerRef.current) {
                nativePlayerRef.current.currentTime = time;
                nativePlayerRef.current.pause();
            }
        });

        newSocket.on('seek', (time) => {
            isSeekingRef.current = true;
            if (playerRef.current && currentUrl) playerRef.current.seekTo(time, 'seconds');
            if (nativePlayerRef.current) nativePlayerRef.current.currentTime = time;
            setTimeout(() => { isSeekingRef.current = false; }, 500);
        });

        newSocket.on('set-url', (url) => {
            setCurrentUrl(url);
            setLocalFileUrl(null);
            setIsPlaying(false);
        });

        return () => {
            newSocket.disconnect();
        };
    }, [id, token, username, navigate]);

    const handleUrlSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (socket && urlInput) {
            socket.emit('set-url', { roomId: id, url: urlInput });
            setCurrentUrl(urlInput);
            setLocalFileUrl(null);
            setUrlInput('');
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const url = URL.createObjectURL(file);
            setLocalFileUrl(url);
            setCurrentUrl(null);
            // We don't broadcast the file, only the fact that we are ready to play.
            // Other users need to select the same file locally.
        }
    };

    const getCurrentTime = () => {
        if (currentUrl && playerRef.current) return playerRef.current.getCurrentTime();
        if (nativePlayerRef.current) return nativePlayerRef.current.currentTime;
        return 0;
    };

    const handlePlay = () => {
        if (!isSeekingRef.current && socket) {
            socket.emit('play', { roomId: id, time: getCurrentTime() });
            setIsPlaying(true);
        }
    };

    const handlePause = () => {
        if (!isSeekingRef.current && socket) {
            socket.emit('pause', { roomId: id, time: getCurrentTime() });
            setIsPlaying(false);
        }
    };

    const handleSeek = (e: any) => {
        // For ReactPlayer onSeek
        if (!isSeekingRef.current && socket) {
            socket.emit('seek', { roomId: id, time: e });
        }
    };

    const handleNativeSeek = () => {
        if (!isSeekingRef.current && socket && nativePlayerRef.current) {
            socket.emit('seek', { roomId: id, time: nativePlayerRef.current.currentTime });
        }
    };

    const copyRoomLink = () => {
        navigator.clipboard.writeText(window.location.href);
        alert('Room link copied!');
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white flex flex-col">
            {/* Header */}
            <header className="bg-gray-800 p-4 flex items-center justify-between shadow-md">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white">
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-xl font-bold">Room: {id}</h1>
                    <button onClick={copyRoomLink} className="p-2 hover:bg-gray-700 rounded-lg flex items-center gap-2 text-sm text-gray-300">
                        <Copy className="w-4 h-4" /> Copy Link
                    </button>
                </div>
                <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-gray-400" />
                    <span className="font-medium">{users.length} watching</span>
                </div>
            </header>

            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
                {/* Main Content (Player) */}
                <div className="flex-1 p-4 lg:p-6 flex flex-col items-center justify-center overflow-y-auto">
                    
                    {!currentUrl && !localFileUrl ? (
                        <div className="max-w-2xl w-full bg-gray-800 rounded-2xl p-8 text-center space-y-8">
                            <div>
                                <h2 className="text-2xl font-bold mb-4">Watch an Online Video</h2>
                                <form onSubmit={handleUrlSubmit} className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Link className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                                        <input
                                            type="url"
                                            placeholder="Paste YouTube, Vimeo, or .mp4 URL"
                                            value={urlInput}
                                            onChange={(e) => setUrlInput(e.target.value)}
                                            className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                                        />
                                    </div>
                                    <button type="submit" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold">
                                        Load
                                    </button>
                                </form>
                            </div>

                            <div className="relative">
                                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-700"></div></div>
                                <div className="relative flex justify-center"><span className="bg-gray-800 px-4 text-gray-400">OR</span></div>
                            </div>

                            <div>
                                <h2 className="text-2xl font-bold mb-4">Watch a Local File</h2>
                                <p className="text-sm text-gray-400 mb-4">Everyone in the room needs to select the exact same file from their device to watch in sync.</p>
                                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-600 border-dashed rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <FileVideo className="w-10 h-10 text-gray-400 mb-2" />
                                        <p className="text-sm text-gray-400"><span className="font-semibold">Click to select a video file</span></p>
                                    </div>
                                    <input type="file" accept="video/*" className="hidden" onChange={handleFileSelect} />
                                </label>
                            </div>
                        </div>
                    ) : (
                        <div className="w-full max-w-6xl aspect-video bg-black rounded-lg overflow-hidden shadow-2xl relative">
                            {currentUrl ? (
                                (() => {
                                    const Player = ReactPlayer as any;
                                    return (
                                        <Player
                                            ref={playerRef}
                                            url={currentUrl}
                                            width="100%"
                                            height="100%"
                                            playing={isPlaying}
                                            controls={true}
                                            onPlay={handlePlay}
                                            onPause={handlePause}
                                            onProgress={(progress: any) => {
                                                // onSeek is deprecated in recent react-player versions for some providers
                                                // This is a safety check if we need progress
                                            }}
                                            config={{
                                                youtube: { playerVars: { disablekb: 1 } }
                                            }}
                                        />
                                    );
                                })()
                            ) : localFileUrl ? (
                                <video
                                    ref={nativePlayerRef}
                                    src={localFileUrl}
                                    className="w-full h-full"
                                    controls
                                    onPlay={handlePlay}
                                    onPause={handlePause}
                                    onSeeked={handleNativeSeek}
                                />
                            ) : null}
                            <div className="absolute top-4 right-4 flex gap-2">
                                <button onClick={() => { setCurrentUrl(null); setLocalFileUrl(null); }} className="px-4 py-2 bg-gray-900/80 hover:bg-gray-800 backdrop-blur rounded-lg text-sm font-medium">
                                    Change Video
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Sidebar (Users) */}
                <div className="w-full lg:w-80 bg-gray-800 border-t lg:border-t-0 lg:border-l border-gray-700 flex flex-col">
                    <div className="p-4 border-b border-gray-700">
                        <h3 className="font-semibold text-lg">People in Room ({users.length})</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {users.map(u => (
                            <div key={u.id} className="flex items-center gap-3 bg-gray-700/50 p-3 rounded-lg">
                                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-bold">
                                    {u.username.charAt(0).toUpperCase()}
                                </div>
                                <span className="font-medium">
                                    {u.username} {u.username === username ? '(You)' : ''}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
