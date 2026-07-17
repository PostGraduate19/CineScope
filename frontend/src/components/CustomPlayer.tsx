import { useRef, useEffect, useState } from 'react';
import Hls from 'hls.js';
import * as dashjs from 'dashjs';
import { Play, Pause, Volume2, VolumeX, Maximize, Minimize, Settings, Loader2 } from 'lucide-react';

interface CustomPlayerProps {
    url: string | null;
    localFileUrl: string | null;
    isPlaying: boolean;
    onPlay: () => void;
    onPause: () => void;
    onSeek: (time: number) => void;
    onWaiting: () => void;
    onCanPlay: () => void;
    time: number;
    forceTimeSync?: boolean; // When true, sets video current time
}

interface CustomPlayerProps {
    url: string | null;
    localFileUrl: string | null;
    isPlaying: boolean;
    onPlay: () => void;
    onPause: () => void;
    onSeek: (time: number) => void;
    onWaiting: () => void;
    onCanPlay: () => void;
    onTimeUpdate?: (time: number) => void;
    time: number;
    forceTimeSync?: boolean; // When true, sets video current time
}

export function CustomPlayer({ url, localFileUrl, isPlaying, onPlay, onPause, onSeek, onWaiting, onCanPlay, onTimeUpdate, time, forceTimeSync }: CustomPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [hls, setHls] = useState<Hls | null>(null);
    const [dash, setDash] = useState<dashjs.MediaPlayerClass | null>(null);

    const [levels, setLevels] = useState<{ id: number, height: number }[]>([]);
    const [currentLevel, setCurrentLevel] = useState<number>(-1); // -1 = auto
    const [showSettings, setShowSettings] = useState(false);

    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [isBuffering, setIsBuffering] = useState(false);
    const [showControls, setShowControls] = useState(true);
    let controlsTimeout: NodeJS.Timeout;

    const sourceUrl = url || localFileUrl;

    useEffect(() => {
        if (!videoRef.current || !sourceUrl) return;

        const video = videoRef.current;

        // Clean up previous instances
        if (hls) { hls.destroy(); setHls(null); }
        if (dash) { dash.reset(); setDash(null); }
        setLevels([]);

        if (sourceUrl.endsWith('.m3u8') && Hls.isSupported()) {
            const hlsInstance = new Hls();
            hlsInstance.loadSource(sourceUrl);
            hlsInstance.attachMedia(video);
            hlsInstance.on(Hls.Events.MANIFEST_PARSED, (_event, data) => {
                const availableLevels = data.levels.map((l, i) => ({ id: i, height: l.height }));
                setLevels(availableLevels);
            });
            setHls(hlsInstance);
        } else if (sourceUrl.endsWith('.mpd')) {
            const dashInstance = dashjs.MediaPlayer().create();
            dashInstance.initialize(video, sourceUrl, false);
            dashInstance.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
                const bitrates = dashInstance.getBitrateInfoListFor("video");
                const availableLevels = bitrates.map((b: any, i: number) => ({ id: i, height: b.height }));
                setLevels(availableLevels);
            });
            setDash(dashInstance);
        } else {
            // Standard MP4 / WebM or Local File
            video.src = sourceUrl;
        }

        return () => {
            if (hls) hls.destroy();
            if (dash) dash.reset();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sourceUrl]);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        if (forceTimeSync && Math.abs(video.currentTime - time) > 1) {
            video.currentTime = time;
        }

        if (isPlaying && video.paused) {
            video.play().catch(e => console.log("Play interrupted", e));
        } else if (!isPlaying && !video.paused) {
            video.pause();
        }
    }, [isPlaying, time, forceTimeSync]);

    const handleLevelChange = (levelId: number) => {
        setCurrentLevel(levelId);
        if (hls) {
            hls.currentLevel = levelId;
        } else if (dash) {
            if (levelId === -1) {
                dash.updateSettings({ streaming: { abr: { autoSwitchBitrate: { video: true } } } });
            } else {
                dash.updateSettings({ streaming: { abr: { autoSwitchBitrate: { video: false } } } });
                dash.setQualityFor("video", levelId);
            }
        }
        setShowSettings(false);
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            containerRef.current?.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const handleMouseMove = () => {
        setShowControls(true);
        clearTimeout(controlsTimeout);
        controlsTimeout = setTimeout(() => {
            if (isPlaying) setShowControls(false);
        }, 3000);
    };

    return (
        <div
            ref={containerRef}
            className="relative w-full aspect-video bg-black rounded-3xl overflow-hidden shadow-soft dark:shadow-soft-dark border border-gray-200 dark:border-gray-800 group"
            onMouseMove={handleMouseMove}
            onMouseLeave={() => isPlaying && setShowControls(false)}
        >
            <video
                ref={videoRef}
                className="w-full h-full"
                onClick={() => isPlaying ? onPause() : onPlay()}
                onPlay={onPlay}
                onPause={onPause}
                onWaiting={() => { setIsBuffering(true); onWaiting(); }}
                onCanPlay={() => { setIsBuffering(false); onCanPlay(); }}
                onSeeked={(e) => onSeek((e.target as HTMLVideoElement).currentTime)}
                onTimeUpdate={(e) => onTimeUpdate && onTimeUpdate((e.target as HTMLVideoElement).currentTime)}
            />

            {/* Loading Overlay */}
            {isBuffering && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/40 pointer-events-none">
                    <Loader2 className="w-12 h-12 text-primary-light dark:text-primary-dark animate-spin" />
                </div>
            )}

            {/* Controls Bar */}
            <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6 pt-16 transition-opacity duration-300 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
                <div className="flex items-center gap-4 text-white">
                    <button onClick={() => isPlaying ? onPause() : onPlay()} className="p-3 bg-white/10 hover:bg-white/20 backdrop-blur rounded-2xl shadow-neumorph-light dark:shadow-neumorph-dark transition-all">
                        {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current" />}
                    </button>

                    <div className="flex items-center gap-2 group/vol relative">
                        <button onClick={() => { setIsMuted(!isMuted); if(videoRef.current) videoRef.current.muted = !isMuted; }} className="p-2 hover:bg-white/20 rounded-xl transition-colors">
                            {isMuted || volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                        </button>
                        <input
                            type="range" min="0" max="1" step="0.05" value={isMuted ? 0 : volume}
                            onChange={(e) => {
                                const v = parseFloat(e.target.value);
                                setVolume(v);
                                setIsMuted(v === 0);
                                if(videoRef.current) { videoRef.current.volume = v; videoRef.current.muted = v === 0; }
                            }}
                            className="w-0 opacity-0 group-hover/vol:w-24 group-hover/vol:opacity-100 transition-all duration-300 accent-primary-light"
                        />
                    </div>

                    <div className="flex-1" />

                    {/* Settings / Quality */}
                    {levels.length > 0 && (
                        <div className="relative">
                            <button onClick={() => setShowSettings(!showSettings)} className="p-2 hover:bg-white/20 rounded-xl transition-colors">
                                <Settings className="w-5 h-5" />
                            </button>
                            {showSettings && (
                                <div className="absolute bottom-full right-0 mb-2 bg-gray-900/90 backdrop-blur border border-gray-700 rounded-xl p-2 min-w-32 shadow-soft">
                                    <div className="text-xs font-semibold text-gray-400 mb-2 px-2 uppercase">Quality</div>
                                    <button onClick={() => handleLevelChange(-1)} className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-gray-800 ${currentLevel === -1 ? 'text-primary-light' : 'text-white'}`}>Auto</button>
                                    {levels.map(l => (
                                        <button key={l.id} onClick={() => handleLevelChange(l.id)} className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-gray-800 ${currentLevel === l.id ? 'text-primary-light' : 'text-white'}`}>
                                            {l.height}p
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    <button onClick={toggleFullscreen} className="p-2 hover:bg-white/20 rounded-xl transition-colors">
                        {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
                    </button>
                </div>
            </div>
        </div>
    );
}
