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
            // Allow guest access
            socket.user = { username: `Guest_${Math.floor(Math.random() * 10000)}` };
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
            socket.to(roomId).emit('user-joined', socket.user.username);
            
            // Send current state to the new user
            socket.emit('room-state', room.videoState);
            io.to(roomId).emit('users-update', room.users);
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
            const { roomId, time } = data;
            const room = rooms.get(roomId);
            if (room) {
                room.videoState.playing = false;
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
                     socket.to(roomId).emit('user-left', socket.user.username);
                     io.to(roomId).emit('users-update', room.users);
                     
                     if (room.users.length === 0) {
                         rooms.delete(roomId);
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
