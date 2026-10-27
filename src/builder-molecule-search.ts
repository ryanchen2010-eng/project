type SearchMatch = { cid: number; name: string; formula: string; structure: string; iupacName: string };
type SearchEditor = {
  setMolecule: (structure: string) => Promise<unknown>;
  editor: { struct: () => { isBlank: () => boolean } };
};
type SearchOptions = {
  getEditor: () => SearchEditor | null;
  canImport: () => boolean;
  lockEditor: () => () => void;
  onImported: (match: SearchMatch) => void;
};

/** Search identifies exact PubChem records; it never infers a structure from a formula. */
export class BuilderMoleculeSearch {
  private readonly form: HTMLFormElement;
  private readonly input: HTMLInputElement;
  private readonly submit: HTMLButtonElement;
  private readonly status: HTMLParagraphElement;
  private readonly results: HTMLUListElement;
  private request = 0;
  private controller?: AbortController;
  private ready = false;
  private searching = false;
  private importing = false;
  private loaded = false;

  constructor(private readonly host: HTMLElement, private readonly options: SearchOptions) {
    host.classList.add('builder-molecule-search');
    host.innerHTML = `
      <form aria-label="Find a Molecule for Builder">
        <label for="builder-molecule-name">Load a Molecule by Name</label>
        <div class="builder-search-controls">
          <input id="builder-molecule-name" type="search" maxlength="100" placeholder="e.g. aspirin or caffeine" autocomplete="off" aria-describedby="builder-search-help builder-search-status" disabled />
          <button type="submit" class="secondary-button" disabled>Search PubChem</button>
        </div>
        <p id="builder-search-help">Choose a result to load its editable 2D structure. 3D preview is a separate check.</p>
      </form>
      <p id="builder-search-status" role="status" aria-live="polite">Available when the drawing editor is ready.</p>
      <ul class="builder-search-results" aria-label="Molecule Search Results" hidden></ul>
    `;
    this.form = host.querySelector('form')!;
    this.input = host.querySelector('input')!;
    this.submit = host.querySelector('button')!;
    this.status = host.querySelector('#builder-search-status')!;
    this.results = host.querySelector('ul')!;
    this.form.addEventListener('submit', (event) => { event.preventDefault(); void this.search(); });
    this.input.addEventListener('input', () => {
      this.request += 1;
      this.controller?.abort();
      this.searching = false;
      this.clearResults();
      this.message('');
      this.updateControls();
    });
  }

  setReady(ready: boolean) {
    this.ready = ready;
    this.updateControls();
    if (ready && !this.status.textContent?.includes('loaded')) this.message('Enter a molecule name, then choose the exact compound.');
  }

  drawingChanged() {
    if (this.loaded && !this.importing) {
      this.loaded = false;
      this.message('Drawing edited. Search results identify the original PubChem records, not your modified structure.');
    }
  }

  private updateControls() {
    this.input.disabled = !this.ready || this.importing;
    this.submit.disabled = !this.ready || this.importing || this.searching;
    this.submit.textContent = this.searching ? 'Searching…' : 'Search PubChem';
    this.host.setAttribute('aria-busy', String(this.searching || this.importing));
    this.results.querySelectorAll('button').forEach((button) => { button.disabled = !this.ready || this.importing; });
  }

  private message(text: string, error = false) {
    this.status.textContent = text;
    this.status.classList.toggle('is-error', error);
  }

  private clearResults() { this.results.replaceChildren(); this.results.hidden = true; }

  private async search() {
    if (!this.ready || this.importing) return;
    const query = this.input.value.trim();
    const request = ++this.request;
    this.controller?.abort();
    this.clearResults();
    if (!query || query.length > 100) {
      this.searching = false;
      this.updateControls();
      this.message('Enter a molecule name of 1–100 characters, such as ethanol.', true);
      return;
    }
    const controller = new AbortController();
    this.controller = controller;
    const timeout = window.setTimeout(() => controller.abort(), 35_000);
    this.searching = true;
    this.updateControls();
    this.message('Looking up structures in PubChem…');
    try {
      const response = await fetch(`/api/pubchem/search?q=${encodeURIComponent(query)}`, { signal: controller.signal });
      const payload = await response.json();
      if (request !== this.request) return;
      if (!response.ok || payload?.error) throw new Error(typeof payload?.error === 'string' ? payload.error : 'Molecule search is unavailable. Try again.');
      if (!Array.isArray(payload?.results) || payload.results.length > 20) throw new Error('The search returned an unreadable result. Try another name.');
      const matches: SearchMatch[] = payload.results;
      if (matches.some((match) => !match || !Number.isSafeInteger(match.cid) || match.cid <= 0
        || typeof match.name !== 'string' || !match.name || typeof match.formula !== 'string'
        || (match.iupacName !== undefined && typeof match.iupacName !== 'string')
        || typeof match.structure !== 'string' || !match.structure || match.structure.length > 200_000)) {
        throw new Error('The search returned an incomplete structure. Try another name.');
      }
      this.renderResults(matches);
      this.message(matches.length
        ? `${matches.length} structure${matches.length === 1 ? '' : 's'} found${payload.limited ? ' (first results shown)' : ''}. Check the name, formula and CID, then select Load into Builder.`
        : 'No matching molecule found. Try a common or full chemical name, such as ethanol. Your drawing is unchanged.');
    } catch (error) {
      if (request !== this.request) return;
      this.message(controller.signal.aborted
        ? 'Search timed out. Try again. Your drawing is unchanged.'
        : error instanceof TypeError || error instanceof SyntaxError
          ? 'Molecule search is unavailable. Check the chemistry service and connection, then try again. Your drawing is unchanged.'
          : `${error instanceof Error ? error.message : 'Could not search for this molecule.'} Your drawing is unchanged.`, true);
    } finally {
      window.clearTimeout(timeout);
      if (request === this.request) { this.searching = false; this.updateControls(); }
    }
  }

  private renderResults(matches: SearchMatch[]) {
    const seen = new Set<number>();
    for (const match of matches) {
      if (seen.has(match.cid)) continue;
      seen.add(match.cid);
      const row = document.createElement('li');
      const identity = document.createElement('div');
      const name = document.createElement('strong');
      name.textContent = match.name;
      const detail = document.createElement('span');
      detail.textContent = `${match.formula} · PubChem CID ${match.cid}`;
      identity.append(name, detail);
      if (match.iupacName && match.iupacName !== match.name) {
        const iupac = document.createElement('small');
        iupac.textContent = match.iupacName;
        identity.append(iupac);
      }
      const load = document.createElement('button');
      load.type = 'button';
      load.className = 'secondary-button';
      load.textContent = 'Load into Builder';
      load.setAttribute('aria-label', `Load ${match.name}, CID ${match.cid}, into Builder`);
      load.addEventListener('click', () => { void this.load(match); });
      row.append(identity, load);
      this.results.append(row);
    }
    this.results.hidden = matches.length === 0;
  }

  private async load(match: SearchMatch) {
    const editor = this.options.getEditor();
    if (!this.ready || this.importing || !editor) return;
    if (!this.options.canImport()) {
      this.message('Wait for the current drawing or preview operation to finish, then load the molecule.', true);
      return;
    }
    let release: (() => void) | undefined;
    try {
      // Both the check and confirmation are synchronous: no delayed lookup can
      // replace a drawing that was edited while waiting for search results.
      if (!editor.editor.struct().isBlank()
        && !window.confirm(`Replace the current drawing with ${match.name} (PubChem CID ${match.cid})? Cancel keeps your drawing.`)) {
        this.message('Loading cancelled. Your drawing is unchanged.');
        return;
      }
      this.importing = true;
      this.updateControls();
      this.message(`Loading ${match.name} into the 2D editor…`);
      release = this.options.lockEditor();
      // Use the selected record's isomeric structure, never name/formula guessing
      // or the 3D SDF endpoint (which is unavailable for some valid 2D structures).
      await editor.setMolecule(match.structure);
      this.options.onImported(match);
      this.loaded = true;
      this.message(`${match.name} (PubChem CID ${match.cid}) loaded. Edit the structure or select Check + preview 3D.`);
    } catch {
      this.message('The editor could not load this structure. Check your drawing before retrying or choose another result.', true);
    } finally {
      release?.();
      this.importing = false;
      this.updateControls();
    }
  }
}
