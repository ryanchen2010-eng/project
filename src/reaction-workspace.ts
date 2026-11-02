import { mountWorkspaceShell } from './workspace-shell';

/** Presentation only: move the live controls, never copy a chemistry fixture. */
export function mountResearchWorkspace(shell: HTMLElement) {
  const get = <T extends HTMLElement = HTMLElement>(selector: string): T => {
    const node = shell.querySelector<T>(selector);
    if (!node) throw new Error(`Missing workspace control: ${selector}`);
    return node;
  };
  const node = <K extends keyof HTMLElementTagNameMap>(tag: K, className: string, text = '') => {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    return element;
  };
  const button = (label: string, action: () => void) => {
    const element = node('button', 'research-button', label);
    element.type = 'button';
    element.addEventListener('click', action);
    return element;
  };
  document.body.classList.add('reaction-research-page');
  shell.classList.add('lab-research');
  const header = get('.lab-header');
  mountWorkspaceShell(shell);
  const copy = get('.lab-copy');
  copy.textContent = 'Choose a pathway. Inspect the chemistry.';
  const headerActions = node('div', 'research-header-actions');
  header.append(headerActions);
  get('.lab-flow').hidden = true;

  // Examples/reference remain the actual collection, behind keyboard-native dialogs.
  const makeDialog = (title: string, content: HTMLElement, openerLabel: string) => {
    const dialog = node('dialog', 'research-dialog');
    const titleNode = node('h2', '', title);
    titleNode.id = `research-dialog-${openerLabel.toLowerCase().replaceAll(' ', '-')}`;
    dialog.setAttribute('aria-labelledby', titleNode.id);
    const top = node('div', 'research-dialog-header');
    top.append(titleNode, button('Close', () => dialog.close()));
    dialog.append(top, content);
    shell.append(dialog);
    const opener = button(openerLabel, () => dialog.showModal());
    opener.setAttribute('aria-haspopup', 'dialog');
    headerActions.append(opener);
    return dialog;
  };
  const examples = makeDialog('Reaction examples', get('.example-library'), 'Examples');
  examples.addEventListener('click', event => {
    if ((event.target as Element).closest('button[data-example]')) {
      examples.close();
      pathways.open = true;
    }
  });
  const guide = get<HTMLDetailsElement>('.reaction-guide');
  guide.open = true;
  makeDialog('Reaction reference', guide, 'Reaction guide');

  const workspace = get('.lab-workspace');
  const inputPanel = get('.lab-input-panel');
  const stage = get('.lab-result-panel');
  const form = get<HTMLFormElement>('#reactant-form');
  const command = node('section', 'research-command');
  workspace.append(command);
  command.setAttribute('aria-label', 'Reactants and selected conditions');
  const inputTitle = inputPanel.querySelector<HTMLElement>('.panel-heading')!;
  inputTitle.querySelector('h2')!.textContent = 'Reactants';
  command.append(inputTitle, form);
  const context = node('div', 'research-context');
  const contextText = node('p', '', 'Conditions not specified');
  const conditionsButton = button('Edit conditions', () => openInspector('conditions', true));
  context.append(node('span', 'eyebrow', 'Conditions'), contextText, conditionsButton);
  command.append(context);

  // The inspector owns the existing conditions and exact product-information nodes.
  const inspector = node('details', 'research-inspector');
  workspace.append(inspector);
  const desktop = window.matchMedia('(min-width: 1100px)');
  inspector.open = desktop.matches;
  desktop.addEventListener('change', event => { inspector.open = event.matches; });
  inspector.append(node('summary', 'research-inspector-heading', 'Inspector'));
  const inspectorButtons = node('div', 'research-panel-switch');
  inspectorButtons.setAttribute('role', 'group');
  inspectorButtons.setAttribute('aria-label', 'Inspector section');
  inspector.append(inspectorButtons);
  const inspectorPanes = new Map<string, HTMLElement>();
  const inspectorControls = new Map<string, HTMLButtonElement>();
  const openInspector = (key: string, focus = false) => {
    inspector.open = true;
    inspectorPanes.forEach((pane, id) => { pane.hidden = key !== id; });
    inspectorControls.forEach((control, id) => control.setAttribute('aria-pressed', String(key === id)));
    if (key === 'product') get<HTMLDetailsElement>('#result-details').open = true;
    if (focus) inspectorControls.get(key)?.focus({ preventScroll: true });
    if (focus && !window.matchMedia('(min-width: 1100px)').matches) inspector.scrollIntoView({ block: 'start', behavior: 'instant' });
  };
  for (const [key, label] of [['product', 'Product'], ['atom', 'Atom'], ['conditions', 'Conditions']]) {
    const pane = node('section', 'research-inspector-pane');
    pane.id = `research-inspector-${key}`;
    pane.hidden = key !== 'conditions';
    pane.setAttribute('aria-label', `${label} inspector`);
    const control = button(label, () => openInspector(key));
    control.setAttribute('aria-controls', pane.id);
    control.setAttribute('aria-pressed', String(key === 'conditions'));
    inspectorButtons.append(control);
    inspector.append(pane);
    inspectorPanes.set(key, pane);
    inspectorControls.set(key, control);
  }
  const conditionsPane = inspectorPanes.get('conditions')!;
  conditionsPane.append(get('.condition-group'), get('#guided-conditions'), get('#reaction-pathway-settings'), form.querySelector('details.field-help')!);
  const productPane = inspectorPanes.get('product')!;
  const productEmpty = node('p', 'research-empty', 'Select a reaction pathway to inspect its exact product structure and limitations.');
  const productDetails = get<HTMLDetailsElement>('#result-details');
  productDetails.open = true;
  productPane.append(productEmpty, productDetails, get('#result-learning'), get('.lab-limits'));
  const atomPane = inspectorPanes.get('atom')!;
  atomPane.append(node('h3', '', 'Mapped atom'));
  const atomText = node('p', 'research-empty', 'Hover or select an atom in a molecular view.');
  const clearAtom = get<HTMLButtonElement>('#clear-atom');
  const clearMirror = button('Clear atom selection', () => clearAtom.click());
  clearMirror.disabled = true;
  atomPane.append(atomText, clearMirror, node('p', 'research-fine-print', 'Linked highlighting follows the existing atom map. 3D displays the main product only; leaving groups and other byproducts may appear only in 2D.'));

  const pathways = node('details', 'research-pathways');
  workspace.append(pathways);
  pathways.open = true;
  const pathwaySummary = node('summary', '', 'Reaction pathways');
  const selectedPathwayLabel = node('span', 'research-selected-pathway');
  const pathwayCount = node('span', 'research-pathway-count');
  pathwaySummary.append(selectedPathwayLabel, pathwayCount);
  const pathwayBody = node('div', 'research-pathway-body');
  pathwayBody.append(get('#reaction-options'), get('#pathway-comparison'));
  pathways.append(pathwaySummary, pathwayBody);
  get('#reaction-options').addEventListener('click', event => {
    if ((event.target as Element).closest('.reaction-option')) {
      pathways.open = false;
      // Keep keyboard focus visible after collapsing the option that was used.
      // Background re-matching uses synthetic clicks and must not steal focus.
      if (event.isTrusted) pathwaySummary.focus({ preventScroll: true });
    }
  });
  const oldStageHeading = stage.querySelector('.panel-heading')!;
  oldStageHeading.remove();
  const status = get('#lab-status');
  const confidence = get('#condition-assessment');
  const confidenceStrip = node('section', 'research-confidence');
  confidenceStrip.setAttribute('aria-label', 'Reaction status and confidence');
  const confidenceDetails = node('details', 'research-confidence-details');
  const confidenceSummary = node('summary', '', 'Model confidence and limitations');
  confidenceDetails.append(confidenceSummary, confidence);
  const reviewConditions = button('Review conditions', () => openInspector('conditions', true));
  confidenceStrip.append(status, confidenceDetails, reviewConditions);
  const net = node('div', 'research-net');
  net.append(get('.equation-label'), get('#reaction-equation'), get('#formula-note'));
  const toolbar = get('.preview-toolbar');
  const run = get('#run-reaction');
  toolbar.append(run);
  const preview = get('#reaction-previews');
  const afterPreview = ['#viewer-hint', '#product-measurements', '#atom-inspection', '#bond-summary', '#bond-legend', '#diagram-note'].map(selector => get(selector));

  const dock = node('section', 'research-dock');
  dock.setAttribute('aria-label', 'Reaction tools');
  const dockButtons = node('div', 'research-panel-switch');
  dockButtons.setAttribute('role', 'group');
  dockButtons.setAttribute('aria-label', 'Reaction tool');
  dock.append(dockButtons);
  const dockPanes = new Map<string, HTMLElement>();
  const dockControls = new Map<string, HTMLButtonElement>();
  const openDock = (key: string) => {
    dockPanes.forEach((pane, id) => { pane.hidden = key !== id; });
    dockControls.forEach((control, id) => control.setAttribute('aria-pressed', String(key === id)));
    // A hidden mechanism must not leave electron-role highlights on the net view.
    if (key !== 'mechanism') get<HTMLDetailsElement>('#reaction-mechanism').open = false;
    for (const details of dockPanes.get(key)?.querySelectorAll<HTMLDetailsElement>(':scope > details') ?? []) details.open = true;
  };
  for (const [key, label, selector, empty] of [
    ['mechanism', 'Mechanism', '#reaction-mechanism', 'Select a pathway to see mapped mechanism steps where implemented. Some pathways provide net bond changes only.'],
    ['amounts', 'Reaction amounts', '#reaction-calculator', 'Choose a supported equation to calculate theoretical amounts.'],
    ['groups', 'Functional groups', '#reactant-groups', 'Inspect functional groups in the selected reactant structures.'],
  ]) {
    const pane = node('div', 'research-dock-pane');
    pane.id = `research-tool-${key}`;
    pane.hidden = key !== 'mechanism';
    const content = get<HTMLDetailsElement>(selector);
    content.open = true;
    const placeholder = node('p', 'research-empty', empty);
    pane.append(placeholder, content);
    if (key === 'amounts') {
      const shortcuts = node('section', 'research-compound-tools');
      shortcuts.append(node('h3', '', 'Other calculators'));
      for (const [selector, label] of [['#reactant-a-calculators', 'Molecule 1'], ['#reactant-b-calculators', 'Molecule 2']]) {
        const row = node('div', '');
        row.append(node('span', '', label), get(selector));
        shortcuts.append(row);
      }
      pane.append(shortcuts);
    }
    const observer = new MutationObserver(() => { placeholder.hidden = !content.hidden && content.childElementCount > 0; });
    observer.observe(content, { attributes: true, attributeFilter: ['hidden'], childList: true });
    const control = button(label, () => openDock(key));
    control.setAttribute('aria-controls', pane.id);
    control.setAttribute('aria-pressed', String(key === 'mechanism'));
    dockButtons.append(control);
    dock.append(pane);
    dockPanes.set(key, pane);
    dockControls.set(key, control);
  }
  stage.replaceChildren(confidenceStrip, net, toolbar, preview, ...afterPreview, dock);
  workspace.replaceChildren(command, inspector, pathways, stage);
  const notice = get('.lab-notice');
  notice.textContent = 'Theoretical reaction models · Not a prediction, experimental yield or laboratory procedure.';

  const refresh = () => {
    const settings = ['#reaction-solvent', '#reaction-temperature', '#reaction-catalyst'].map(selector => get<HTMLSelectElement>(selector));
    const entered = settings.filter(select => select.value).map(select => select.selectedOptions[0]?.textContent ?? '');
    contextText.textContent = entered.length ? entered.join(' · ') : 'Conditions not specified';
    const count = get('#reaction-options').querySelectorAll('.reaction-option').length;
    const selected = get('#reaction-options').querySelector('.reaction-option[aria-pressed="true"]');
    if (!selected) pathways.open = true;
    selectedPathwayLabel.textContent = selected ? ` · ${selected.querySelector('strong')?.textContent ?? 'Selected'}` : '';
    pathwayCount.textContent = count ? `${count} available` : '';
    atomText.textContent = get('#atom-status').textContent;
    clearMirror.disabled = clearAtom.disabled;
    productEmpty.hidden = !productDetails.hidden;
    productEmpty.textContent = selected
      ? 'The net product is shown in the equation and 2D view. Generate a supported 3D product for molecular details.'
      : 'Select a reaction pathway to inspect its exact product structure and limitations.';
    reviewConditions.hidden = confidence.hidden;
    confidenceDetails.hidden = confidence.hidden;
    // Keep the exact confidence tier visible, with the full explanation available.
    confidenceSummary.textContent = confidence.textContent?.split(' — ')[0] || 'Model confidence and limitations';
    confidenceSummary.className = confidence.className;
  };
  const observer = new MutationObserver(refresh);
  for (const selector of ['#lab-status', '#condition-assessment', '#reaction-options', '#atom-status', '#clear-atom', '#result-details']) {
    observer.observe(get(selector), { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['hidden', 'disabled'] });
  }
  workspace.addEventListener('change', refresh);
  refresh();
  return { openDock, openInspector };
}
