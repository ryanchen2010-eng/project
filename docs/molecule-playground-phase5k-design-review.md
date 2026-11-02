# Molecule Playground — Phase 5K product design review

Date: 22 October 2026. Status: **proposal only; awaiting a design choice**.

## Executive decision

Recommend **Scientific Workbench, with Guided Chemistry Studio's condition-review flow**. Keep the compact expert inspector as an optional detail surface, not the default experience.

The current site is not primarily suffering from its colors. It has useful individual components, but the page composition still behaves like several independently developed prototypes. Reaction Lab gives setup, reference examples, warnings and results similar visual weight, while the molecule—the reason to use the tool—arrives late or occupies a relatively small effective area.

The proposed direction changes the hierarchy: **selected chemistry in the center; setup beside it; precise details on demand**. On phones, switch between Workspace, Setup and Details rather than stacking every input and example above the result. This remains a practical chemistry tool, not a quiz or a forced lesson.

The newly reported Br/O lone-pair crowding, Br⁻ centering and overlapping atom circles are real diagram presentation defects. They should receive a small, independently verified renderer repair before or alongside any approved layout implementation. They are **not fixed in production by this review**.

## Scope and preservation

- Reviewed the actual local website, including all five pages, at measured CSS viewports of **1440 × 1000** and **390 × 844**.
- Created isolated HTML/CSS/JavaScript proposals under `docs/phase5k/`; none is a Vite production entry point.
- Did not alter production UI, chemistry rules, RDKit, molecular identities, atom mapping, stereochemistry, calculators, Guided Conditions backend, existing tests, curated examples or the fixed 347-case benchmark.
- Did not stage, commit, push, merge, access/change Render, update the release branch or change the frozen Beta v1.
- Existing dirty working files were preserved. This review is against the current local files, not a claim that they equal a remote or deployed version.

## 1. Evidence: current rendered interface

### Capture index

Each link is a real local browser capture, not an AI-generated approximation.

| Page | Desktop | Mobile | Observed issue |
|---|---|---|---|
| Home | [Desktop](phase5k/current-home-desktop.png) | [Mobile](phase5k/current-home-mobile.png) | Large editorial hero and decorative water illustration precede equal access to all four tools. |
| Explorer | [Desktop](phase5k/current-explorer-desktop.png) | [Mobile](phase5k/current-explorer-mobile.png) | The sample list takes precedence over the selected molecule, especially on phones. |
| Builder | [Desktop](phase5k/current-builder-desktop.png) | [Mobile](phase5k/current-builder-mobile.png) | Large editor and nested headings push the primary preview action down; preview has less emphasis. |
| Reaction Lab | [Initial desktop](phase5k/current-reaction-desktop.png) | [Initial mobile](phase5k/current-reaction-mobile.png) | Matching pathways follow conditions, functional-group inspection and the example library. |
| Calculators | [Desktop](phase5k/current-calculators-desktop.png) | [Mobile](phase5k/current-calculators-mobile.png) | Repeated page/card introductions delay the actual amount input. |

Additional evidence: [current selected SN2 comparison](phase5k/current-reaction-compare-desktop.png), [current mechanism capture](phase5k/current-mechanism-desktop.png), and [measured viewport observations](phase5k/viewport-observations.json).

The Builder capture has a visible keyboard-focus outline after using its existing “Skip to workspace” link. That is not proposed decorative styling. Browser zoom was left unchanged; viewport dimensions were verified from the DOM. Older supplementary `*-desktop-full.png` captures in this folder are not the normalized viewport evidence used above.

### Measured workflow, not an invented usability score

At 390px CSS width, once the current Reaction Lab catalog had loaded:

| Element | Document position |
|---|---:|
| Example-library heading | 1,593px |
| Pathway options | 2,268px |
| Reaction diagram | 2,950px |

These are one observed empty-workflow state, not fixed dimensions across all reactions. Selecting a pathway, opening guidance or showing a mechanism changes height. They demonstrate a composition problem: the phone can have no horizontal overflow and still require several screens of navigation before chemistry appears. No participant study, task completion time or quantitative satisfaction rating was conducted.

### What should be retained

The green identity is recognizable. Existing controls have useful labels; the 2D/3D/Compare modes, exact identities, theoretical-confidence wording, mapped mechanisms, calculations and scientific restrictions are valuable. The redesign should make these easier to find, not replace them or relax their meaning.

## 2. Specific critique, separated by problem type

Codes: **A** styling; **B** component hierarchy; **C** layout; **D** workflow; **E** visualization integration. Several issues span more than one category.

| Observation | Why it hurts | Type | Proposed response |
|---|---|---|---|
| Global header varies between Home, Explorer, Builder, Reaction Lab and Calculators. Explorer's large title is the brand rather than the active tool. | The user repeatedly has to infer where they are. Similar buttons do not compensate for a different application shell. | B/C | One compact, persistent tool navigation; active tool title and shared header spacing. |
| Home prioritizes a large slogan, water illustration and two calls to action. | Returning users must pass promotional composition to reach the tools; Reaction Lab and Calculators feel secondary. The three decorative dots resemble a carousel control. | B/D | Tool-first landing area with four equal task entries; illustration secondary and explicitly non-interactive. |
| Explorer's sample library precedes the model on mobile. | Selecting a compound still leaves users among samples rather than at the selected structure. | C/D/E | Search remains accessible; selected model first; samples in a compact picker/drawer on narrow screens. |
| Explorer can contain a very small molecule in a large blank viewer. | Container size is not usable visualization size. The page appears empty even when the model loaded successfully. | E | Fit-to-visible-atoms policy with bounded camera padding; test tiny and large compounds independently. Do not change coordinates. |
| Builder's wrapper includes multiple introductions above a tall Ketcher editor; Check + preview 3D is near its bottom. | The action needed after drawing is detached from the task and can leave the phone viewport. | B/C/D | Keep the action near the editor toolbar or a keyboard-safe task bar; collapse instructional copy. Preserve Ketcher commands and draft behavior. |
| Ketcher has its own visual language, surrounded by large application cards. | The editor reads as an embedded product, not a seamless working surface. | A/B | Align wrapper borders, spacing and toolbar baseline. Do not casually retheme or replace editor internals. |
| Calculators repeats brand, page title, topic title, explanatory text and an optional compound card. | On mobile, users encounter a large amount of framing before the first quantity. | B/D | Compact topic/context header, grouped amount + unit fields, result region close to Calculate. Existing arithmetic untouched. |
| Reaction Lab includes title, notice, guide, static three-step bar and two large panel titles before the working content. | Several surfaces compete to explain the same journey; chrome consumes space needed for the chemistry. | B/C | One short task title and one persistent confidence summary. Keep the guide reachable but secondary. |
| “03 Result” appears beside “01 Reactants,” while “02” is farther down the first column. | Numbering implies a vertical sequence the layout does not follow. | B/D | Either a real step workflow or a true workbench; do not mix static step decoration with spatial panels. |
| Conditions such as oxidation stage appear before knowing whether the selected pathway needs them. | Irrelevant fields increase cognitive load and suggest chemistry settings have universal relevance. | B/D | Pathway-contextual condition summary; retain all backend fields and conflict review. Never silently replace settings when hiding controls. |
| Twenty example cards sit between inputs and matching options. | Reference material interrupts the core input → option → result flow. | B/C/D | Compact example chooser; pathways directly follow selected inputs. Do not add benchmark molecules to examples. |
| Compare changes the left/right allocation, making the input area substantially narrower. | Mode changes move familiar controls and wrap labels, destabilizing the user's spatial context. | C/E | Stable outer panel geometry; only the central stage changes modes. |
| Current SN2 comparison uses visibly different bond scales for separate species. | A small substrate and a very long isolated O–H depiction look inconsistent; visual size is determined by component fitting rather than a coherent scene. | E | Normalize diagram bond/font scale before packing species, then fit the composed scene. This is not a claim about measured bond lengths. |
| Viewer camera controls form a large wrapping toolbar outside the main visual focus. | Controls compete with the molecule and can travel far from it on phones. | B/E | Small in-view camera toolbar with explicit Fit; secondary controls in an accessible menu. Keep drag, zoom, measurement and keyboard alternatives. |
| Mechanism and product detail accordions follow multiple confidence notes, diagrams and viewer controls. | Inspecting electron movement feels like leaving the reaction rather than changing its perspective. | B/E | Adjacent mechanism dock and shared selected-atom inspector. Do not mislabel net edits as elementary mechanisms. |
| Repeated long confidence messages appear in option details, status, equation, diagram and information surfaces. | Users learn to skip repeated copy, including important distinctions. | B/D | One always-visible state + actionable next step; detailed reasons, sources and limitations remain available. Never collapse the fact that 3D is blocked. |

### Atom circles and electrons: confirmed presentation defects

The user's two screenshots are consistent with the locally reproduced SN2 mechanism fixture. The [before/after spacing proposal](phase5k/proposal-atom-spacing-detail.png) directly addresses this feedback.

Source inspection confirms that the current net renderer uses a fixed 24px atom font, 18px glow, 17px hit circle and 21px reaction-site circle. Lone pairs are placed at radii 23px or 26px, based only on one- versus multi-letter element symbols. The placement algorithm avoids bond directions and other chosen pair angles, **not the actual glyph/charge bounds or neighboring disconnected-species annotations**. The mechanism renderer draws a combined, potentially disconnected graph into one 560 × 230 state.

Consequences and a safe future repair:

1. **Br is wider than C/O.** A fixed circular halo can be cramped; several simultaneous source/destination/site/selection rings make it worse. Derive visual bounds from the rendered label and compose highlight states into one intelligible treatment. Keep a separate adequately sized invisible hit target.
2. **Charge affects perceived centering.** Lone pairs should be anchored to the base element's atom position. Render charge as a distinct superscript with reserved space, rather than centering the entire `Br⁻` label as if it were one symmetric glyph. Confirm RDKit's actual glyph bounds/anchor before changing overlays.
3. **Lone pairs need annotation-aware clearance.** Respect element, charge, isotope, explicit-H, bond, wedge and neighboring-atom bounds. Enlarging every circle or moving every pair by one constant is not a general fix.
4. **Disconnected fragments need annotation-aware packing.** Reserve an explicit gap or plus separator between bromomethane and hydroxide. The current Br/O crowding can suggest a bond that is not present. The verified starting-state graph has C1–Br2 and O6–H7, **not Br2–O6**.
5. **Do not change electron bookkeeping.** This SN2 fixture has three Br lone pairs before departure, four on Br⁻ afterward, three on hydroxide O and two on methanol O. Dots are Lewis bookkeeping, not 3D orbital orientation.

The proposed drawing demonstrates these principles for **one verified fixture only**. It is not a generalized production renderer, does not establish a solution for every element/charge and does not add a new reaction. Future implementation must cover net diagrams, functional-group views and mechanism states together, while preserving graph identity and map-based picking.

## 3. Three competing design directions

### A. Scientific Workbench

**Core layout:** compact shared top navigation; 264px setup column; largest central 2D/3D workspace; 252px inspector. Setup includes identities, matching pathway and contextual conditions. Examples and functional groups are disclosures, not interruptions.

**Journey:** choose exact compounds → choose a structural pathway → resolve required conditions → inspect central diagram/model → inspect mechanism or mapped atom. The result never becomes an unrelated page.

**Visualization:** stable central stage with 2D, 3D and Compare modes; in-view camera actions; immediately adjacent mechanism dock; product/atom/conditions inspector. The net equation includes byproducts even though the 3D view shows only the main product.

**Advantages:** strongest balance of tool efficiency, approachable hierarchy and persistent visual context; room for existing confidence safeguards. Fits students, teachers and occasional university users without imposing a lesson sequence.

**Tradeoffs:** three columns can become cramped on ordinary laptops; inspector must move to a reachable drawer or lower panel at intermediate widths. Long compound names and multiple pathway options need explicit handling.

**Mobile:** default to one readable molecular mode, with Workspace/Setup/Details switching and a compact current-input summary. Compare can stack the two views deliberately; it must not shrink both into unreadable columns. A mobile 3D screenshot is provided separately.

### B. Guided Chemistry Studio

**Core layout:** four real stages—Inputs, Conditions, Pathway, Inspect. At Inspect, remove the permanent input column and retain an editable reaction summary above a broad visual canvas and product inspector.

**Journey:** progressively complete the reaction context, then inspect. Stages remain revisitable; users do not have to re-enter compounds to change conditions.

**Visualization:** widest inspect canvas of the three concepts; mechanism follows the visual stage, not the example library. Short reviewed-input summary preserves context.

**Advantages:** clearest onboarding and missing-condition recovery; a teacher can demonstrate an understandable sequence. It need not become a quiz or a study lesson.

**Tradeoffs:** repeated reactions and expert comparisons incur extra navigation; a mandatory wizard can obscure valid partially specified structural options. The backend's eligibility/condition distinction must not be turned into artificial sequential chemistry.

**Mobile:** four compact stage controls and one working surface at a time. Return-to-inspection action stays explicit. The prototype's early stages show read-only fixture setup, not a finished editor workflow.

### C. Professional Research Interface

**Core layout:** narrow dark tool rail; compact reactant/reagent/conditions command row; large molecular stage; dense inspector; bottom detail dock with Pathways, Mechanism, Mapping and Amounts.

**Journey:** adjust context in the command row, select/compare options in the dock, inspect molecular changes and map details without leaving the visual center.

**Visualization:** central stage with concise surrounding chrome; mapping/stoichiometry detail separate from the product summary. The rail makes application navigation persistent.

**Advantages:** efficient for repeated use, structural comparison and map-level inspection. Strongest conventional scientific-software appearance.

**Tradeoffs:** compact labels and multiple tool surfaces create a learning curve; the rail costs horizontal space; “research” appearance must not imply universal prediction or experimental validation. Too dense as the only default for high-school users.

**Mobile:** rail becomes a Tools menu, command row condenses and details become secondary panels. Do not simply shrink a desktop data table.

### Recommendation: A + bounded parts of B

Choose **A as the application structure**, B's explicit review/confirmation for Guided Conditions, and C's optional map/details density. Do not ship three permanent competing modes: that would multiply maintenance and navigation ambiguity. The three prototypes are alternatives for choosing a direction.

## 4. Visual mockups and interactive proposal

Open the local [design comparison prototype](http://127.0.0.1:5173/docs/phase5k/proposals.html) while the existing local server is running. File sources: [HTML](phase5k/proposals.html), [CSS](phase5k/proposals.css), [JavaScript](phase5k/proposals.js).

| Direction | Desktop mockup | Mobile mockup |
|---|---|---|
| Scientific Workbench | [Desktop](phase5k/proposal-workbench-desktop.png) | [Mobile 2D](phase5k/proposal-workbench-mobile.png), [Mobile 3D](phase5k/proposal-workbench-mobile-3d.png) |
| Guided Chemistry Studio | [Desktop](phase5k/proposal-studio-desktop.png) | [Mobile](phase5k/proposal-studio-mobile.png) |
| Professional Research Interface | [Desktop](phase5k/proposal-research-desktop.png) | [Mobile](phase5k/proposal-research-mobile.png) |

Additional states: [atom spacing before/after](phase5k/proposal-atom-spacing-detail.png), [mechanism controls](phase5k/proposal-mechanism-detail.png), [incomplete conditions](phase5k/proposal-conditions-incomplete.png), [review confirmation](phase5k/proposal-conditions-review.png), [condition-complete fixture](phase5k/proposal-conditions-complete.png).

### Chemistry provenance and honest prototype boundaries

All three concepts use the same existing supported example: **bromomethane + hydroxide → methanol + bromide**, SN2, selected polar-aprotic model conditions. Map IDs come from the existing public match/diagram/run functions. O6 attacks C1 and C1–Br2 bond electrons go to Br2 in **one concerted step**; no carbocation is invented. This methyl example makes no new stereochemical claim.

The second fixture uses the existing **2-propanol / sodium hypochlorite** model. Generic aqueous conditions leave the 2D view conditional and block 3D. The review dialog lists actual guidance requirements, including the qualified acetic-acid profile. Confirmation changes to a **separately validated static display fixture**, not a live backend calculation or automatic condition substitution.

Fixture generator: [capture-fixtures.py](phase5k/capture-fixtures.py). Display data: [fixtures.json](phase5k/fixtures.json). The generator refuses to overwrite its fixture output. The source production chemistry functions were not changed.

| Demonstrated in the isolated proposal | Not implemented / not claimed |
|---|---|
| Three genuinely different panel/workflow arrangements | A production redesign or new route |
| Actual verified product Molfile in 3Dmol | A different conformer generator or predicted experimental geometry |
| 2D/3D/Compare, fit, zoom and rotation | Full production measurement controls or saved camera persistence |
| Map-based 2D selection and main-product 3D correspondence | Arbitrary new structures or universal diagram collision solving |
| Br byproduct correctly reports no main-product 3D counterpart | A fabricated 3D bromide counterpart in the methanol model |
| Product/Atom/Conditions and mechanism/detail controls | Complete production focus/state management for every pathway |
| Incomplete/reviewed/condition-complete fixture states | Chemistry service calls from the prototype or laboratory procedures |
| Calculator access to the existing page | New arithmetic, quantity transfer or an asserted experimental yield |

## 5. Design-system recommendations

UI/UX Pro Max influenced the move toward a restrained, high-density scientific workspace: consistent shell, clear hierarchy, semantic feedback, progressive disclosure and accessible interaction. Search output was treated as design input, not a mandate. The generic hero/CTA landing template, orange marketing palette and decorative treatment were rejected for the chemistry workspace. The local progressive-disclosure search did not return a useful match; the skill's built-in quick reference was used rather than claiming that search validated the design.

- **Identity:** retain deep green; warm/neutral white working surfaces; restrained borders. No gradients behind chemical labels and no decorative motion competing with structures.
- **Typography:** one application sans-serif stack, 14–16px task text, 22–26px page titles, tabular numerals for measured quantities. Preserve proper formula subscripts, charge superscripts, unit spacing and distinguish compound name from molecular formula. Do not equate matching formulas with identity.
- **Spacing:** 4/8/12/16/24px scale. Group controls by task rather than giving every paragraph a separate card. Use 6–10px component radii instead of mixing oversized pills with nested cards.
- **Semantic colors:** green = supported model state, amber = action/review needed, red = error or broken bond only with a label, blue = formed bond, purple = selected atom. Mechanism electron-source/destination must have labels and a legend; reuse existing meanings rather than silently reassigning colors.
- **Contrast:** validate every text/state combination, including disabled controls and SVG annotations. Color alone must not encode scientific confidence or a bond change. The prototype palette is a direction, not a complete accessibility certification.
- **Controls:** visible keyboard focus; native buttons/selects/dialog where practical; 44px coarse-pointer controls and 16px phone form inputs. Provide a reachable mapped-atom list for dense diagrams where small individual atoms cannot become 44px targets without overlapping.
- **Interaction:** hover is transient; click/tap pins; clear pin returns to hover. Do not rebuild the whole diagram/WebGL scene on every pointer movement. Preserve current map IDs and avoid stealing focus or replacing a pinned atom during camera drag.
- **Motion:** no required decorative animation; respect reduced motion. Auto-rotation off by default and explicit when on.
- **Sources and limitations:** keep short state labels and immediate next actions visible; put detailed model assumptions/references in a consistent inspector. Preserve scientifically essential warnings even when shortening copy.

### Visualization and feedback state contract

| State | Proposed presentation | Must not happen |
|---|---|---|
| Empty | Central “Choose compounds to see supported pathways,” with a concise example-picker action | Large blank viewer mistaken for failure |
| Structure resolution/loading | Specific text naming the current operation; stable reserved canvas; cancel/retry where supported | Stale product shown as if it belongs to new inputs |
| Structural option, missing conditions | Amber summary + Review conditions action; visibly conditional 2D; disabled 3D with reason | Successful-looking 3D or generic “unfavorable” label |
| Qualified supported model | Net products/byproducts + concise theoretical status + detailed limitations available | “Guaranteed product,” experimental yield/rate, or safety assurance |
| Unsupported model | Precise site/environment/condition reason and supported next action | “Cannot react” when the software merely cannot represent it |
| Rendering/library failure | Retain valid 2D data; explain 3D rendering failure independently from chemistry | Reclassifying a renderer failure as a chemical rejection |
| Network/API failure | Request-specific retry and retained user inputs; previous result visibly outdated | Silent reuse of earlier conditions or another compound's product |

The table is a design specification. Not every state is interactively implemented in the static proposal.

## 6. Prioritized implementation proposal — not executed

| Order | Deliverable | Verification before moving on |
|---|---|---|
| 0 | Confirm one direction. Treat diagram annotation repair as a separately scoped rendering change. | User approval; production baseline preserved; no chemistry-rule edits. |
| 1 | Label-aware atom highlights, charge/lone-pair clearance, disconnected-fragment packing and consistent diagram scale. | Br/Br⁻, O/O⁻/O⁺, Cl, N/N⁺, isotope/H labels, carbonyls, wedges and crowded mechanism states; electron counts/maps unchanged; no label/charge/bond collisions. |
| 2 | Shared compact shell and one Reaction Lab workbench skeleton. | All five navigation/return routes work; no global CSS leakage into Ketcher/Calculators; 320px, tablet and desktop checks. |
| 3 | Move example picker below/away from primary matching flow; contextual setup and selectable pathways beside the stage. | Multiple sites, orientations and faces remain separately selectable; no auto-selection implying experimental preference; exact identities retained. |
| 4 | Integrate stable view modes, atom inspector and nearby mechanism dock. | Mapped atom equality, byproduct handling, keyboard/touch behavior, camera/measurement persistence, WebGL resize and no hover rebuild/jitter. |
| 5 | Integrate existing Guided Conditions, not a replacement condition engine. | Incomplete/conflicting states block asserted products; explicit confirmation; backend revalidation after edits; stale results cleared; no silent profile reuse. |
| 6 | Adapt the chosen structure to phones and intermediate widths. | Workspace-first; Setup/Details discoverable; keyboard does not hide actions; long names, many options and enlarged text remain usable. |
| 7 | Apply shared shell/spacing to Explorer, Builder, Home and Calculators in separate small changes. | Existing property displays, ionic handling, editor drafts, cross-page molecule transfer and arithmetic preserved. |
| 8 | Final regression, confidence and visual review before any release discussion. | Full existing test suite, TypeScript, build, fixed benchmark and condition-aware checks; public match/diagram/run parity; no release without separate approval. |

Do not tie a low-risk diagram fix to a wholesale layout rewrite. Conversely, another round of border/color adjustments alone will not fix the example-library interruption or mobile result ordering.

## 7. Risks to existing functionality

1. **State coupling:** moving DOM nodes may detach event handlers or duplicate compound/condition state. Preserve one source of truth and current invalidation behavior.
2. **Scientific confidence:** a compact inspector can accidentally hide conditional status. Keep blocking state and next action on the main workspace in every breakpoint.
3. **Mapping:** regenerating a depiction must not reorder or guess atom identity from element symbols. Retain map IDs through SVG, diagram controls and exact product Molfile.
4. **Stereochemistry:** visual re-layout must preserve wedges, charges and labels. Camera orientation is not a new stereochemical assignment; SN2 inversion tests still apply independently of this methyl mockup.
5. **Annotations:** moving lone pairs for readability must not change their count or imply orbital direction. Fragment packing must preserve actual connectivity and avoid fake contact bonds.
6. **WebGL lifecycle:** hidden tabs/panels have zero size; refit/resize at the right time without discarding user camera state or measurements. Test large compounds, not just methanol.
7. **Accessibility:** canvas needs textual equivalents; atom interaction needs keyboard/touch alternatives; panel switches need announced state and intentional focus. The prototype is not a finished accessibility implementation.
8. **Mobile:** three columns cannot merely become three long sections. Preserve access to conditions/product limitations even when the inspector is not permanently visible.
9. **Calculators and editor:** presentation-only changes can still break imports, exact-identity transfer, units, forms, drafts and focus. Do not refactor those scientific modules as part of a layout task.
10. **Deployment boundary:** these files are local design artifacts. Choosing a design does not authorize pushing, merging, changing Beta v1 or deploying to Render.

## 8. Verification and stopping point

- Existing production, test, public, benchmark and script files covered by the pre-review SHA256 inventory remained byte-for-byte unchanged: **242 checked files**.
- Branch remains `codex/ui-ux-improvements-v1`; Git index and recorded HEAD, main and frozen-beta refs unchanged.
- Prototype JavaScript syntax checked with the bundled Node runtime.
- Verified static fixtures use existing public match/diagram/run functions; SN2 and qualified oxidation generated balanced product records; incomplete oxidation did not run asserted 3D generation.
- Visually checked desktop/mobile proposals and atom-spacing comparison; all three concepts had no horizontal overflow at 320px CSS width.
- Checked mobile Setup/Workspace switching, 2D/3D mode switching, keyboard Br selection and honest absent-main-product correspondence, and confirmation-gated Guided Conditions fixture switching.
- No console errors were reported in the reviewed proposal session. This is not exhaustive browser/device coverage.
- **3,792 tests passing is the supplied/completed Phase 5J baseline, not a new Phase 5K regression run.** Full chemistry regression, TypeScript and production build were not rerun for these isolated documentation/prototype files. No new coverage claim is made for the fixed 347-case benchmark.
- New files were checked for trailing whitespace. No production implementation, push or deployment was performed.

**Stop here.** Select A, B, C or the recommended A+B hybrid before a production redesign. A narrowly scoped atom-label/electron-spacing repair can be approved independently.
