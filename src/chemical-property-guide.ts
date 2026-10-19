import type { ChemicalPropertyKey } from './chemical-descriptions';

export interface ChemicalPropertyGuideEntry {
  key: ChemicalPropertyKey;
  label: string;
  definition: string;
  source: { label: string; url: string };
}

/** Flexible registry: a compound only supplies reviewed, relevant properties. */
export const PROPERTY_GUIDE: readonly ChemicalPropertyGuideEntry[] = [
  {
    key: 'state',
    label: 'Physical state',
    definition: 'Solid, liquid, or gas under stated conditions. These notes use 25°C and 1 atm unless specified otherwise.',
    source: {
      label: 'OpenStax · Phases of matter',
      url: 'https://openstax.org/books/chemistry/pages/1-2-phases-and-classification-of-matter',
    },
  },
  {
    key: 'appearance',
    label: 'Appearance',
    definition: 'A substance’s visible colour and form; appearance alone cannot identify a compound.',
    source: {
      label: 'OpenStax · Physical and chemical properties',
      url: 'https://openstax.org/books/chemistry-2e/pages/1-3-physical-and-chemical-properties',
    },
  },
  {
    key: 'solubility',
    label: 'Water solubility',
    definition: 'How much dissolves in water under stated conditions. Miscible liquids mix in all proportions; gas solubility also depends on pressure.',
    source: {
      label: 'OpenStax · Solubility',
      url: 'https://openstax.org/books/chemistry/pages/11-3-solubility',
    },
  },
  {
    key: 'density',
    label: 'Density',
    definition: 'Mass per volume, with phase and temperature specified where available.',
    source: {
      label: 'OpenStax · Measurements',
      url: 'https://openstax.org/books/chemistry-2e/pages/1-4-measurements',
    },
  },
  {
    key: 'functionalGroups',
    label: 'Functional groups',
    definition: 'Recognizable atom groups associated with characteristic organic reactions, such as alcohol, carbonyl, ester, and carboxylic-acid groups.',
    source: {
      label: 'OpenStax · Functional groups',
      url: 'https://openstax.org/books/organic-chemistry/pages/3-1-functional-groups',
    },
  },
  {
    key: 'hydrogenBonding',
    label: 'Hydrogen bonding',
    definition: 'Donors provide a suitably bonded hydrogen; acceptors provide an electron pair. These are attractions, not the molecule’s covalent bonds.',
    source: {
      label: 'OpenStax · Intermolecular forces',
      url: 'https://openstax.org/books/chemistry-2e/pages/10-1-intermolecular-forces',
    },
  },
  {
    key: 'flammability',
    label: 'Flammability',
    definition: 'Whether and how readily a substance burns under stated conditions. An oxidizer can support burning without being a fuel.',
    source: {
      label: 'ACS · Chemical hazards',
      url: 'https://institute.acs.org/acs-center/lab-safety/hazard-assessment/tools/common-hazards.html',
    },
  },
  {
    key: 'reactivity',
    label: 'Reactivity',
    definition: 'Behaviour with particular chemical partners under particular conditions, not one universal reaction rating.',
    source: {
      label: 'IUPAC · Reactivity',
      url: 'https://goldbook.iupac.org/terms/view/R05180',
    },
  },
  {
    key: 'toxicity',
    label: 'Toxicity',
    definition: 'Potential harmful effects depend on dose, exposure route, and duration; these brief notes are not a safety assessment.',
    source: {
      label: 'National Research Council · Toxicity and exposure',
      url: 'https://www.ncbi.nlm.nih.gov/books/NBK222198/',
    },
  },
  {
    key: 'acidity',
    label: 'Acidity / basicity',
    definition: 'pH describes a solution, not an isolated molecule. It depends on concentration, composition, and temperature.',
    source: {
      label: 'OpenStax · pH and pOH',
      url: 'https://openstax.org/books/chemistry-2e/pages/14-2-ph-and-poh',
    },
  },
  {
    key: 'oxidation',
    label: 'Oxidation / corrosion',
    definition: 'Oxidation increases oxidation state, often through electron loss. Metal rusting is only one example.',
    source: {
      label: 'IUPAC · Oxidation',
      url: 'https://goldbook.iupac.org/terms/view/O04362',
    },
  },
  {
    key: 'combustion',
    label: 'Combustion behaviour',
    definition: 'Whether burning occurs and its main products. These qualitative notes are not numerical heats of combustion.',
    source: {
      label: 'OpenStax · Combustion and enthalpy',
      url: 'https://openstax.org/books/chemistry-2e/pages/5-3-enthalpy',
    },
  },
  {
    key: 'stability',
    label: 'Stability',
    definition: 'How heat, light, moisture, or other conditions can alter or decompose a substance; stability is condition-dependent.',
    source: {
      label: 'ACS · Chemical hazards',
      url: 'https://institute.acs.org/acs-center/lab-safety/hazard-assessment/tools/common-hazards.html',
    },
  },
];
