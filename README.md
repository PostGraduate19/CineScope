# Watch Party PWA

A cross-platform Progressive Web App that lets you watch videos in perfect sync with your friends, across mobile and desktop devices. It supports synchronizing online video URLs (like YouTube) and local video files.

## Features

- **Cross-Platform & Installable:** Built as a PWA, so it runs in any browser and can be installed natively on iOS, Android, Windows, and macOS.
- **Dual-Mode Player:**
  - *Online Videos:* Paste a YouTube, Vimeo, or MP4 URL.
  - *Local Videos:* Select a video file from your device. If everyone in the room selects the same file, it will sync playback!
- **Real-time Synchronization:** Ensures everyone is at the exact same timestamp. Pausing, playing, and seeking are synced instantly via WebSockets.
- **Guest Mode:** Join rooms instantly without needing to create an account.

## How to Run Locally in VS Code

You need [Node.js](https://nodejs.org/) installed on your machine.

1. Open this project folder in VS Code.
2. Open the integrated terminal (\`Ctrl + \`\` or \`Cmd + \`\`).
3. Install all dependencies across the frontend and backend by running:
   \`\`\`bash
   npm run install:all
   \`\`\`
4. Start both the backend and frontend servers concurrently by running:
   \`\`\`bash
   npm start
   \`\`\`
5. Open your browser and navigate to the frontend URL shown in the terminal (usually \`http://localhost:5173\`).

### Testing Sync Locally

To test synchronization by yourself:
1. Open \`http://localhost:5173\` in a normal browser tab (e.g., Chrome).
2. Open a **Private/Incognito** window and navigate to \`http://localhost:5173\` again.
3. Log in as a Guest on both windows with different names.
4. Create a room on Window 1, and copy the Room ID.
5. Join that Room ID on Window 2.
6. Load a video and press play—watch them sync!