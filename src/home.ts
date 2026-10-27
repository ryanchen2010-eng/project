import { mountWorkspaceShell, workspaceIcon } from './workspace-shell';
import './workspace-shell.css';

const shell = document.querySelector<HTMLElement>('.home-shell');
if (!shell) throw new Error('Home workspace was not found.');
mountWorkspaceShell(shell);
for (const card of shell.querySelectorAll('.tool-card')) {
  const symbol = card.querySelector('.tool-symbol');
  const route = card.querySelector('a')?.getAttribute('href');
  if (symbol && route) symbol.replaceChildren(workspaceIcon(route));
}
