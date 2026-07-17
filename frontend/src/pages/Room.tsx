import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io, Socket } from 'socket.io-client';
// @ts-ignore
import ReactPlayer from 'react-player';
import { useAuth } from '../contexts/AuthContext';
import { Link, FileVideo, Copy, ArrowLeft, Sun, Moon } from 'lucide-react';
import { Sidebar } from '../components/Sidebar';
import { CustomPlayer } from '../components/CustomPlayer';
import { useTheme } from '../contexts/ThemeContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

interface User {
    id: string;
    username: string;
}

export function Room() {
    const { id } = useParams<{ id: string }>();
    const { token, username } = useAuth();
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    
    const [socket, setSocket] = useState<Socket | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [hostId, setHostId] = useState<string>('');
    const [urlInput, setUrlInput] = useState('');
    const [currentUrl, setCurrentUrl] = useState<string | null>(null);
    const [localFileUrl, setLocalFileUrl] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [serverTime, setServerTime] = useState(0);
    const [forceTimeSync, setForceTimeSync] = useState(false);

    const isSeekingRef = useRef(false);
    const playerTimeRef = useRef(0);

    useEffect(() => {
        if (!username) {
            navigate('/login');
            return;
        }

        const newSocket = io(API_URL, {
            auth: { token, username } // pass username for guest access
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
                setServerTime(state.time);
                setForceTimeSync(true);
                setTimeout(() => setForceTimeSync(false), 500);
            }, 500);
        });

        newSocket.on('users-update', (data: { users: User[], host: string } | User[]) => {
            if (Array.isArray(data)) {
                // Should not happen if backend is updated correctly, but just in case
                setUsers(data);
            } else {
                setUsers(data.users);
                setHostId(data.host);
            }
        });

        newSocket.on('play', (time) => {
            isSeekingRef.current = true;
            setServerTime(time);
            setForceTimeSync(true);
            setIsPlaying(true);
            setTimeout(() => {
                isSeekingRef.current = false;
                setForceTimeSync(false);
            }, 500);
        });

        newSocket.on('pause', (time) => {
            isSeekingRef.current = true;
            setServerTime(time);
            setForceTimeSync(true);
            setIsPlaying(false);
            setTimeout(() => {
                isSeekingRef.current = false;
                setForceTimeSync(false);
            }, 500);
        });

        newSocket.on('seek', (time) => {
            isSeekingRef.current = true;
            setServerTime(time);
            setForceTimeSync(true);
            setTimeout(() => {
                isSeekingRef.current = false;
                setForceTimeSync(false);
            }, 500);
        });

        newSocket.on('force-pause', ({ reason: _reason, username: _username }) => {
            isSeekingRef.current = true;
            setIsPlaying(false);
            setTimeout(() => { isSeekingRef.current = false; }, 500);
            // Force pause locally without overwriting server state
            if (playerTimeRef.current > 0) {
                 newSocket.emit('pause', { roomId: id, time: playerTimeRef.current, isForcePause: true });
            }
        });

        newSocket.on('resume-play', () => {
            setIsPlaying(true);
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

    const handlePlay = () => {
        if (!isSeekingRef.current && socket) {
            socket.emit('play', { roomId: id, time: playerTimeRef.current });
            setIsPlaying(true);
        }
    };

    const handlePause = () => {
        if (!isSeekingRef.current && socket) {
            socket.emit('pause', { roomId: id, time: playerTimeRef.current });
            setIsPlaying(false);
        }
    };

    // Need to hook this to CustomPlayer onTimeUpdate if we want precise play/pause state

    const handleSeek = (time: number) => {
        playerTimeRef.current = time;
        if (!isSeekingRef.current && socket) {
            socket.emit('seek', { roomId: id, time });
        }
    };

    const copyRoomLink = () => {
        navigator.clipboard.writeText(window.location.href);
        alert('Room link copied!');
    };

    return (
        <div className="min-h-screen flex flex-col transition-colors duration-300">
            {/* Header */}
            <header className="bg-surface-light dark:bg-surface-dark p-4 flex items-center justify-between shadow-soft dark:shadow-soft-dark z-10">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/')} className="text-gray-600 dark:text-gray-400 hover:text-primary-light dark:hover:text-primary-dark transition-colors">
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                    <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Room: {id}</h1>
                    <button onClick={copyRoomLink} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 transition-colors shadow-neumorph-light dark:shadow-neumorph-dark active:shadow-neumorph-light-inset dark:active:shadow-neumorph-dark-inset">
                        <Copy className="w-4 h-4" /> Copy Link
                    </button>
                </div>
                <div className="flex items-center gap-4">
                    <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors shadow-neumorph-light dark:shadow-neumorph-dark active:shadow-neumorph-light-inset dark:active:shadow-neumorph-dark-inset">
                        {theme === 'dark' ? <Sun className="w-5 h-5 text-gray-100" /> : <Moon className="w-5 h-5 text-gray-900" />}
                    </button>
                </div>
            </header>

            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
                {/* Main Content (Player) */}
                <div className="flex-1 p-4 lg:p-6 flex flex-col items-center justify-center overflow-y-auto bg-background-light dark:bg-background-dark">
                    
                    {!currentUrl && !localFileUrl ? (
                        <div className="max-w-2xl w-full bg-surface-light dark:bg-surface-dark rounded-3xl p-10 text-center space-y-8 shadow-neumorph-light dark:shadow-neumorph-dark">
                            <div>
                                <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100">Watch an Online Video</h2>
                                <form onSubmit={handleUrlSubmit} className="flex gap-4">
                                    <div className="relative flex-1">
                                        <Link className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400 w-5 h-5" />
                                        <input
                                            type="url"
                                            placeholder="Paste YouTube, Vimeo, or .mp4 URL"
                                            value={urlInput}
                                            onChange={(e) => setUrlInput(e.target.value)}
                                            className="w-full pl-12 pr-4 py-4 bg-transparent border-none rounded-2xl text-gray-900 dark:text-gray-100 focus:outline-none shadow-neumorph-light-inset dark:shadow-neumorph-dark-inset placeholder-gray-500 dark:placeholder-gray-500"
                                        />
                                    </div>
                                    <button type="submit" className="px-8 py-4 bg-primary-light dark:bg-primary-dark text-white rounded-2xl font-semibold shadow-neumorph-light dark:shadow-neumorph-dark active:shadow-neumorph-light-inset dark:active:shadow-neumorph-dark-inset transition-all">
                                        Load
                                    </button>
                                </form>
                            </div>

                            <div className="relative">
                                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-300 dark:border-gray-700"></div></div>
                                <div className="relative flex justify-center"><span className="bg-surface-light dark:bg-surface-dark px-4 text-gray-500 dark:text-gray-400 font-medium">OR</span></div>
                            </div>

                            <div>
                                <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100">Watch a Local File</h2>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">Everyone in the room needs to select the exact same file from their device to watch in sync.</p>
                                <label className="flex flex-col items-center justify-center w-full h-40 rounded-3xl cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-900/50 transition-colors shadow-neumorph-light-inset dark:shadow-neumorph-dark-inset border-2 border-transparent hover:border-primary-light/30 dark:hover:border-primary-dark/30">
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <FileVideo className="w-12 h-12 text-primary-light dark:text-primary-dark mb-3" />
                                        <p className="text-base text-gray-700 dark:text-gray-300 font-medium">Click to select a video file</p>
                                    </div>
                                    <input type="file" accept="video/*" className="hidden" onChange={handleFileSelect} />
                                </label>
                            </div>
                        </div>
                    ) : (
                        <div className="w-full max-w-6xl relative">
                            <CustomPlayer
                                url={currentUrl}
                                localFileUrl={localFileUrl}
                                isPlaying={isPlaying}
                                onPlay={handlePlay}
                                onPause={handlePause}
                                onSeek={handleSeek}
                                onWaiting={() => socket?.emit('buffering', { roomId: id, isBuffering: true })}
                                onCanPlay={() => socket?.emit('buffering', { roomId: id, isBuffering: false })}
                                onTimeUpdate={(t: number) => playerTimeRef.current = t}
                                time={serverTime}
                                forceTimeSync={forceTimeSync}
                            />
                            <div className="absolute top-4 right-4 flex gap-2 z-20">
                                <button onClick={() => { setCurrentUrl(null); setLocalFileUrl(null); }} className="px-4 py-2 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-xl text-sm font-medium text-white transition-colors border border-white/10">
                                    Change Video
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Sidebar (Chat & Participants) */}
                <Sidebar socket={socket} roomId={id || ''} users={users} hostId={hostId} />
            </div>
        </div>
    );
}
