const socketIo = require('socket.io');
const jwt = require('jsonwebtoken');
const { SECRET_KEY } = require('./auth');

function setupSocket(server) {
    const io = socketIo(server, {
        cors: {
            origin: "*", // Adjust for production
            methods: ["GET", "POST"]
        }
    });

    const rooms = new Map(); // Store room state

    io.use((socket, next) => {
        const token = socket.handshake.auth.token;
        if (token) {
            jwt.verify(token, SECRET_KEY, (err, decoded) => {
                if (err) return next(new Error('Authentication error'));
                socket.user = decoded;
                next();
            });
        } else {
            // Allow guest access with the username provided by the frontend if any, otherwise random guest
            const guestName = socket.handshake.auth.username || `Guest_${Math.floor(Math.random() * 10000)}`;
            socket.user = { username: guestName };
            next();
        }
    });

    io.on('connection', (socket) => {
        console.log(`User connected: ${socket.user.username} (${socket.id})`);

        socket.on('join-room', (roomId) => {
            socket.join(roomId);
            console.log(`${socket.user.username} joined room: ${roomId}`);

            // Initialize room state if it doesn't exist
            if (!rooms.has(roomId)) {
                rooms.set(roomId, {
                    users: [],
                    host: socket.id,
                    bufferingUsers: new Set(),
                    videoState: {
                        playing: false,
                        time: 0,
                        url: null // Only for online URLs
                    }
                });
            }

            const room = rooms.get(roomId);
            room.users.push({ id: socket.id, username: socket.user.username });
            
            // Notify others in the room
            socket.to(roomId).emit('user-joined', { id: socket.id, username: socket.user.username });
            
            // Send current state to the new user
            socket.emit('room-state', room.videoState);
            io.to(roomId).emit('users-update', { users: room.users, host: room.host });
        });

        // Chat
        socket.on('chat-message', ({ roomId, message }) => {
            io.to(roomId).emit('chat-message', {
                id: Math.random().toString(36).substr(2, 9),
                userId: socket.id,
                username: socket.user.username,
                text: message,
                timestamp: Date.now()
            });
        });

        // WebRTC Signaling
        socket.on('signal', ({ peerId, signal }) => {
            io.to(peerId).emit('signal', {
                peerId: socket.id,
                signal
            });
        });

        // Buffering State (Latency Auto-Pause)
        socket.on('buffering', ({ roomId, isBuffering }) => {
            const room = rooms.get(roomId);
            if (!room) return;

            if (isBuffering) {
                room.bufferingUsers.add(socket.id);
                if (room.bufferingUsers.size === 1) { // First user to buffer
                    // Do not change room.videoState.playing here, just tell clients to pause temporarily
                    io.to(roomId).emit('force-pause', { reason: 'buffering', username: socket.user.username });
                }
            } else {
                room.bufferingUsers.delete(socket.id);
                if (room.bufferingUsers.size === 0 && room.videoState.playing) { // Everyone is ready
                    io.to(roomId).emit('resume-play');
                }
            }
        });

        // Host Controls
        socket.on('kick-user', ({ roomId, userId }) => {
            const room = rooms.get(roomId);
            if (room && room.host === socket.id) {
                io.to(userId).emit('kicked');
            }
        });

        socket.on('mute-user', ({ roomId, userId, type }) => {
            const room = rooms.get(roomId);
            if (room && room.host === socket.id) {
                io.to(userId).emit('muted', { type }); // type: 'audio' | 'video'
            }
        });

        socket.on('play', (data) => {
            const { roomId, time } = data;
            const room = rooms.get(roomId);
            if (room) {
                room.videoState.playing = true;
                room.videoState.time = time;
                socket.to(roomId).emit('play', time);
            }
        });

        socket.on('pause', (data) => {
            const { roomId, time, isForcePause } = data;
            const room = rooms.get(roomId);
            if (room) {
                if (!isForcePause) {
                    room.videoState.playing = false;
                }
                room.videoState.time = time;
                socket.to(roomId).emit('pause', time);
            }
        });

        socket.on('seek', (data) => {
            const { roomId, time } = data;
            const room = rooms.get(roomId);
            if (room) {
                room.videoState.time = time;
                socket.to(roomId).emit('seek', time);
            }
        });

        socket.on('set-url', (data) => {
             const { roomId, url } = data;
             const room = rooms.get(roomId);
             if (room) {
                 room.videoState.url = url;
                 room.videoState.playing = false;
                 room.videoState.time = 0;
                 socket.to(roomId).emit('set-url', url);
             }
        });

        socket.on('disconnecting', () => {
             socket.rooms.forEach(roomId => {
                 const room = rooms.get(roomId);
                 if (room) {
                     room.users = room.users.filter(u => u.id !== socket.id);
                     room.bufferingUsers?.delete(socket.id);

                     socket.to(roomId).emit('user-left', socket.id);
                     
                     if (room.users.length === 0) {
                         rooms.delete(roomId);
                     } else {
                         // Reassign host if host left
                         if (room.host === socket.id) {
                             room.host = room.users[0].id;
                         }
                         io.to(roomId).emit('users-update', { users: room.users, host: room.host });

                         // If we were waiting on this user to buffer, check if we can resume
                         if (room.bufferingUsers.size === 0 && room.videoState.playing) {
                             io.to(roomId).emit('resume-play');
                         }
                     }
                 }
             });
        });

        socket.on('disconnect', () => {
            console.log(`User disconnected: ${socket.user.username} (${socket.id})`);
        });
    });
}

module.exports = setupSocket;
