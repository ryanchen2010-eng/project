/** Ketcher focuses its off-screen clipboard during mount and draft restoration.
 * Keep only the initializing editor inert; never reset the user's scroll/focus. */
export function guardEditorStartup(host: HTMLElement, frame = requestAnimationFrame): () => void {
  const wasInert = host.inert;
  host.inert = true;
  host.setAttribute('aria-busy', 'true');
  let released = false;
  return () => {
    if (released) return;
    released = true;
    frame(() => frame(() => {
      host.inert = wasInert;
      host.removeAttribute('aria-busy');
    }));
  };
}
