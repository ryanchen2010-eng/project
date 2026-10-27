/** Camera-only alternatives to dragging/scrolling; never changes a molecular graph. */
export type CameraViewer = {
  zoomTo: () => unknown;
  zoom: (factor: number) => unknown;
  rotate: (degrees: number, axis: string) => unknown;
  render: () => unknown;
};

export function mountViewerControls(host: HTMLElement, viewer?: CameraViewer) {
  const bar = document.createElement('div');
  bar.className = 'viewer-controls';
  bar.setAttribute('role', 'group');
  bar.setAttribute('aria-label', '3D view controls');
  const actions: [string, () => void][] = [
    ['Fit molecule', () => { viewer?.zoomTo(); }],
    ['Zoom in', () => { viewer?.zoom(1.2); }],
    ['Zoom out', () => { viewer?.zoom(1 / 1.2); }],
    ['Rotate left', () => { viewer?.rotate(-15, 'y'); }],
    ['Rotate right', () => { viewer?.rotate(15, 'y'); }],
    ['Rotate up', () => { viewer?.rotate(-15, 'x'); }],
    ['Rotate down', () => { viewer?.rotate(15, 'x'); }],
  ];
  const buttons = actions.map(([name, act]) => {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = name; button.disabled = true;
    button.setAttribute('aria-label', name);
    button.title = name;
    const paths: Record<string, string> = {
      'Zoom in': '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5M7 10h6m-3-3v6"/>',
      'Zoom out': '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5M7 10h6"/>',
      'Rotate left': '<path d="M5 8h9a6 6 0 0 1 0 12M9 4 5 8l4 4"/>',
      'Rotate right': '<path d="M19 8h-9a6 6 0 0 0 0 12M15 4l4 4-4 4"/>',
      'Rotate up': '<path d="M8 5v9a6 6 0 0 0 12 0M4 9l4-4 4 4"/>',
      'Rotate down': '<path d="M8 19v-9a6 6 0 0 1 12 0M4 15l4 4 4-4"/>',
    };
    if (paths[name]) button.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
    button.addEventListener('click', () => {
      if (button.disabled || !viewer) return;
      act(); viewer.render();
    });
    bar.append(button);
    return button;
  });
  host.insertAdjacentElement('afterend', bar);
  return {
    setEnabled(enabled: boolean) { for (const button of buttons) button.disabled = !enabled || !viewer; },
    setVisible(visible: boolean) { bar.hidden = !visible; },
  };
}
