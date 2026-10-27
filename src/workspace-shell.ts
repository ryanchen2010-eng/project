/** Shared presentation chrome. Existing route links and tool nodes stay intact. */
const ICONS: Record<string, string> = {
  '/': '<path d="m3 10 9-7 9 7v10H6V10m4 10v-7h4v7"/>',
  '/explore.html': '<circle cx="7" cy="6" r="3"/><circle cx="18" cy="9" r="3"/><circle cx="9" cy="19" r="3"/><path d="m10 7 5 1M8 9l1 7m3 2 4-6"/>',
  '/builder.html': '<path d="m4 16 12-12 4 4L8 20H4v-4m9-9 4 4"/>',
  '/reaction-lab.html': '<path d="M9 3h6m-5 0v7L4 20h16l-6-10V3M7 15h10"/>',
  '/calculators.html': '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 11h1m3 0h1m3 0h1M8 15h1m3 0h1m3 0h1M8 19h1m3 0h1m3 0h1"/>',
};

export function workspaceIcon(route: string): SVGSVGElement {
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  icon.setAttribute('viewBox', '0 0 24 24');
  icon.setAttribute('aria-hidden', 'true');
  icon.setAttribute('focusable', 'false');
  icon.classList.add('workspace-icon');
  icon.innerHTML = ICONS[route] ?? ICONS['/explore.html'];
  return icon;
}

export function mountWorkspaceShell(shell: HTMLElement): void {
  if (shell.querySelector(':scope > .workspace-rail')) return;
  const nav = shell.querySelector<HTMLElement>('nav[aria-label="Project pages"]');
  if (!nav) throw new Error('The workspace requires its existing project navigation.');
  const header = nav.closest('header');
  document.body.classList.add('workspace-page');
  shell.classList.add('workspace-shell');
  nav.classList.add('workspace-nav');
  const rail = document.createElement('aside');
  rail.className = 'workspace-rail research-rail';
  const brand = shell.querySelector<HTMLAnchorElement>('.site-brand') ?? document.createElement('a');
  brand.className = 'workspace-brand research-brand';
  brand.textContent = 'Molecule\nPlayground';
  brand.href = '/';
  brand.setAttribute('aria-label', 'Molecule Playground home');
  for (const link of nav.querySelectorAll('a')) {
    link.prepend(workspaceIcon(link.getAttribute('href') ?? '/'));
  }
  const note = document.createElement('p');
  note.className = 'workspace-rail-note research-rail-note';
  note.textContent = 'Interactive chemistry workspace';
  rail.append(brand, nav, note);
  shell.prepend(rail);
  // Home and Calculators used a brand-only top header. Do not leave a blank bar.
  if (header && !header.querySelector('h1')) header.hidden = true;
}
