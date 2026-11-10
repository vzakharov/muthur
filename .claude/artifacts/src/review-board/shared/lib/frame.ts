/** `run` deferred to the next animation frame; calls made before it fires coalesce into one. */
export function perFrame(run: () => void): () => void {
  let scheduled = false;
  return () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      run();
    });
  };
}
