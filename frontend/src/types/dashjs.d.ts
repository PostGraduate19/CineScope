declare module 'dashjs' {
    export interface MediaPlayerClass {
        initialize: (view?: HTMLVideoElement, source?: string, autoPlay?: boolean) => void;
        on: (type: string, listener: (e: any) => void, scope?: any) => void;
        getBitrateInfoListFor: (mediaType: string) => any[];
        updateSettings: (settings: any) => void;
        setQualityFor: (type: string, value: number, force?: boolean) => void;
        reset: () => void;
    }

    export const MediaPlayer: {
        (): {
            create(): MediaPlayerClass;
        };
        events: {
            STREAM_INITIALIZED: string;
        };
    };
}
