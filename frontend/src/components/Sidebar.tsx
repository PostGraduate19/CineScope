import React, { useState, useEffect, useRef } from 'react';
import { Send, UserMinus, MicOff, VideoOff, Mic, Video, Users } from 'lucide-react';
import Peer from 'simple-peer';
import { Socket } from 'socket.io-client';
import { useAuth } from '../contexts/AuthContext';

interface User {
    id: string;
    username: string;
}

interface Message {
    id: string;
    userId: string;
    username: string;
    text: string;
    timestamp: number;
}

interface SidebarProps {
    socket: Socket | null;
    roomId: string;
    users: User[];
    hostId: string;
}

export function Sidebar({ socket, roomId, users, hostId }: SidebarProps) {
    const { username } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [msgInput, setMsgInput] = useState('');
    const [localStream, setLocalStream] = useState<MediaStream | null>(null);
    const [micOn, setMicOn] = useState(true);
    const [camOn, setCamOn] = useState(true);
    const peersRef = useRef<{ [peerId: string]: Peer.Instance }>({});
    const [remoteStreams, setRemoteStreams] = useState<{ [peerId: string]: MediaStream }>({});

    const localVideoRef = useRef<HTMLVideoElement>(null);
    const chatEndRef = useRef<HTMLDivElement>(null);

    const isHost = socket?.id === hostId;

    useEffect(() => {
        if (!socket) return;

        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(stream => {
                setLocalStream(stream);
                if (localVideoRef.current) localVideoRef.current.srcObject = stream;
            })
            .catch(err => console.error("Media access denied:", err));

        socket.on('chat-message', (msg: Message) => {
            setMessages(prev => [...prev, msg]);
        });

        socket.on('kicked', () => {
            alert('You have been kicked from the room.');
            window.location.href = '/';
        });

        socket.on('muted', ({ type }) => {
            if (type === 'audio') toggleMic(false);
            if (type === 'video') toggleCam(false);
        });

        return () => {
            socket.off('chat-message');
            socket.off('kicked');
            socket.off('muted');
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            Object.values(peersRef.current).forEach(peer => peer.destroy());
        };
    }, [socket]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const pendingSignalsRef = useRef<{ [peerId: string]: any[] }>({});

    useEffect(() => {
        if (!socket) return;

        // Process any signals that arrived before localStream was ready
        if (localStream) {
            Object.keys(pendingSignalsRef.current).forEach(peerId => {
                const signals = pendingSignalsRef.current[peerId];
                signals.forEach(signal => {
                    let peer = peersRef.current[peerId];
                    if (!peer) {
                        peer = addPeer(signal, peerId, localStream);
                        peersRef.current[peerId] = peer;
                    } else {
                        peer.signal(signal);
                    }
                });
            });
            pendingSignalsRef.current = {};
        }

        const handleUserJoined = (user: {id: string, username: string}) => {
            if (!localStream) return; // Wait until stream is ready to offer
            const peer = createPeer(user.id, socket.id, localStream);
            peersRef.current[user.id] = peer;
        };

        const handleSignal = (data: { peerId: string, signal: any }) => {
            if (!localStream) {
                // Queue the signal if we don't have our stream yet
                if (!pendingSignalsRef.current[data.peerId]) {
                    pendingSignalsRef.current[data.peerId] = [];
                }
                pendingSignalsRef.current[data.peerId].push(data.signal);
                return;
            }
            let peer = peersRef.current[data.peerId];
            if (!peer) {
                peer = addPeer(data.signal, data.peerId, localStream);
                peersRef.current[data.peerId] = peer;
            } else {
                peer.signal(data.signal);
            }
        };

        const handleUserLeft = (peerId: string) => {
            if (peersRef.current[peerId]) {
                peersRef.current[peerId].destroy();
                delete peersRef.current[peerId];
            }
            setRemoteStreams(prev => {
                const next = { ...prev };
                delete next[peerId];
                return next;
            });
        };

        socket.on('user-joined', handleUserJoined);
        socket.on('signal', handleSignal);
        socket.on('user-left', handleUserLeft);

        return () => {
            socket.off('user-joined', handleUserJoined);
            socket.off('signal', handleSignal);
            socket.off('user-left', handleUserLeft);
        };
    }, [socket, localStream]);


    function createPeer(userToSignal: string, _callerID: string | undefined, stream: MediaStream) {
        const peer = new Peer({ initiator: true, trickle: false, stream });
        peer.on('signal', signal => socket?.emit('signal', { peerId: userToSignal, signal }));
        peer.on('stream', remoteStream => setRemoteStreams(prev => ({ ...prev, [userToSignal]: remoteStream })));
        return peer;
    }

    function addPeer(incomingSignal: any, callerID: string, stream: MediaStream) {
        const peer = new Peer({ initiator: false, trickle: false, stream });
        peer.on('signal', signal => socket?.emit('signal', { peerId: callerID, signal }));
        peer.on('stream', remoteStream => setRemoteStreams(prev => ({ ...prev, [callerID]: remoteStream })));
        peer.signal(incomingSignal);
        return peer;
    }


    const sendMsg = (e: React.FormEvent) => {
        e.preventDefault();
        if (!msgInput.trim() || !socket) return;
        socket.emit('chat-message', { roomId, message: msgInput });
        setMsgInput('');
    };

    const toggleMic = (force?: boolean) => {
        if (!localStream) return;
        const newState = force !== undefined ? force : !micOn;
        localStream.getAudioTracks().forEach(track => track.enabled = newState);
        setMicOn(newState);
    };

    const toggleCam = (force?: boolean) => {
        if (!localStream) return;
        const newState = force !== undefined ? force : !camOn;
        localStream.getVideoTracks().forEach(track => track.enabled = newState);
        setCamOn(newState);
    };

    const handleKick = (userId: string) => {
        if (socket) socket.emit('kick-user', { roomId, userId });
    };

    const handleMute = (userId: string, type: 'audio' | 'video') => {
        if (socket) socket.emit('mute-user', { roomId, userId, type });
    };

    return (
        <div className="w-full lg:w-80 bg-surface-light dark:bg-surface-dark border-t lg:border-t-0 lg:border-l border-gray-200 dark:border-gray-800 flex flex-col h-[50vh] lg:h-auto overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-800 shrink-0">
                <div className="flex items-center gap-2 mb-4">
                    <Users className="w-5 h-5 text-primary-light dark:text-primary-dark" />
                    <h3 className="font-semibold text-lg">Participants ({users.length}/4)</h3>
                </div>

                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                    <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden shadow-soft dark:shadow-soft-dark border border-gray-200 dark:border-gray-800">
                        <video ref={localVideoRef} autoPlay muted playsInline className="w-full h-full object-cover" />
                        <div className="absolute bottom-1 left-1 bg-black/60 px-1.5 rounded text-xs text-white flex items-center gap-1">
                            {username} (You)
                        </div>
                        <div className="absolute bottom-1 right-1 flex gap-1">
                            <button onClick={() => toggleMic()} className={`p-1 rounded-full ${micOn ? 'bg-black/60 text-white' : 'bg-red-500 text-white'}`}>
                                {micOn ? <Mic className="w-3 h-3" /> : <MicOff className="w-3 h-3" />}
                            </button>
                            <button onClick={() => toggleCam()} className={`p-1 rounded-full ${camOn ? 'bg-black/60 text-white' : 'bg-red-500 text-white'}`}>
                                {camOn ? <Video className="w-3 h-3" /> : <VideoOff className="w-3 h-3" />}
                            </button>
                        </div>
                    </div>

                    {users.filter(u => u.id !== socket?.id).map(u => (
                        <div key={u.id} className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden shadow-soft dark:shadow-soft-dark border border-gray-200 dark:border-gray-800 group">
                            <VideoPlayer stream={remoteStreams[u.id]} />
                            <div className="absolute bottom-1 left-1 bg-black/60 px-1.5 rounded text-xs text-white flex items-center gap-1">
                                {u.username} {u.id === hostId && '⭐'}
                            </div>

                            {isHost && (
                                <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1">
                                    <button onClick={() => handleMute(u.id, 'audio')} className="p-1 bg-red-500 hover:bg-red-600 rounded text-white" title="Mute Mic"><MicOff className="w-3 h-3" /></button>
                                    <button onClick={() => handleMute(u.id, 'video')} className="p-1 bg-red-500 hover:bg-red-600 rounded text-white" title="Mute Cam"><VideoOff className="w-3 h-3" /></button>
                                    <button onClick={() => handleKick(u.id)} className="p-1 bg-red-600 hover:bg-red-700 rounded text-white" title="Kick"><UserMinus className="w-3 h-3" /></button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <div className="flex-1 flex flex-col min-h-0">
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map(m => (
                        <div key={m.id} className={`flex flex-col ${m.userId === socket?.id ? 'items-end' : 'items-start'}`}>
                            <span className="text-xs text-gray-500 mb-1">{m.userId === socket?.id ? 'You' : m.username}</span>
                            <div className={`px-3 py-2 rounded-2xl max-w-[85%] break-words shadow-soft dark:shadow-soft-dark ${
                                m.userId === socket?.id
                                ? 'bg-primary-light dark:bg-primary-dark text-white rounded-br-none'
                                : 'bg-gray-100 dark:bg-gray-800 rounded-bl-none'
                            }`}>
                                {m.text}
                            </div>
                        </div>
                    ))}
                    <div ref={chatEndRef} />
                </div>
                <form onSubmit={sendMsg} className="p-3 border-t border-gray-200 dark:border-gray-800 flex gap-2 shrink-0">
                    <input
                        type="text"
                        value={msgInput}
                        onChange={e => setMsgInput(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1 bg-transparent border border-gray-300 dark:border-gray-700 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-light dark:focus:ring-primary-dark shadow-neumorph-light-inset dark:shadow-neumorph-dark-inset transition-shadow"
                    />
                    <button type="submit" disabled={!msgInput.trim()} className="p-2 rounded-full bg-primary-light dark:bg-primary-dark text-white shadow-soft dark:shadow-soft-dark disabled:opacity-50">
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </div>
    );
}

const VideoPlayer = ({ stream }: { stream: MediaStream | undefined }) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);
    return <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover bg-gray-900" />;
};
