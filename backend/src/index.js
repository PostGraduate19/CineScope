const express = require('express');
const http = require('http');
const cors = require('cors');
const { router: authRouter } = require('./auth');
const setupSocket = require('./socket');

const app = express();
const server = http.createServer(app);

app.use(cors());
app.use(express.json());

app.use('/auth', authRouter);

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

setupSocket(server);

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
