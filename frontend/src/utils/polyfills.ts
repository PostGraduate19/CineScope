// simple-peer needs global object and Buffer
if (typeof window !== 'undefined') {
  (window as any).global = window;
  // Make a dummy Buffer for simple-peer if needed (though Vite usually handles it, sometimes we need to polyfill)
  (window as any).Buffer = (window as any).Buffer || require('buffer').Buffer;
}
