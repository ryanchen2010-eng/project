export type ChemicalPropertyKey =
  | 'flammability'
  | 'reactivity'
  | 'toxicity'
  | 'acidity'
  | 'oxidation'
  | 'combustion'
  | 'state'
  | 'appearance'
  | 'solubility'
  | 'density'
  | 'functionalGroups'
  | 'hydrogenBonding'
  | 'stability';

export interface ChemicalProfile {
  cid: number;
  overview: string;
  uses: string;
  properties: Partial<Record<ChemicalPropertyKey, string>>;
  sources: { label: string; url: string }[];
}

const icsc = (name: string, card: string) => ({
  label: `ILO / WHO: ${name}`,
  url: `https://inchem.org/documents/icsc/icsc/eics${card}.htm`,
});

const alcohols = {
  label: 'NOAA: Alcohols and polyols',
  url: 'https://cameochemicals.noaa.gov/react/4',
};
const alkanes = {
  label: 'NOAA: Saturated hydrocarbons',
  url: 'https://cameochemicals.noaa.gov/react/29',
};
const hydrogenBonds = {
  label: 'OpenStax: Hydrogen bonding',
  url: 'https://openstax.org/books/chemistry-2e/pages/10-1-intermolecular-forces',
};
const functionalGroups = {
  label: 'OpenStax: Functional groups',
  url: 'https://openstax.org/books/organic-chemistry/pages/3-1-functional-groups',
};

// Compact teaching notes checked against linked sources on 2026-10-01.
// State is for 25°C and 1 atm unless a value explicitly states otherwise.
// Optional fields are omitted when unreviewed; never infer them from a name.
// These notes are not exposure limits, handling advice, or full safety records.
// Aqueous pH is solution-specific. Combustion entries are qualitative behaviour,
// not measured heats of combustion. Preserve conditions with numeric values.
export const chemicalProfiles: ChemicalProfile[] = [
  {
    cid: 962,
    overview: 'A polar solvent essential to life and many chemical reactions.',
    uses: 'Drinking; washing; cooking; solvent.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Practically colourless',
      density: '≈1.00 g/mL at 4°C',
      hydrogenBonding: 'Donor and acceptor',
      flammability: 'Nonflammable',
      reactivity: 'Reacts with some metals and water-sensitive chemicals',
      toxicity: 'Excess intake can disrupt electrolyte balance',
      acidity: 'Pure water: pH ≈7 at 25°C',
      oxidation: 'Water and dissolved oxygen contribute to metal corrosion',
      combustion: 'Noncombustible; common combustion product',
    },
    sources: [
      { label: 'USGS: Water properties', url: 'https://www.usgs.gov/special-topics/water-science-school/science/water-properties-information-topic' },
      { label: 'USGS: Water density', url: 'https://www.usgs.gov/water-science-school/science/water-density' },
      { label: 'NOAA: Water and aqueous solutions', url: 'https://cameochemicals.noaa.gov/react/100' },
      { label: 'USGS: Measuring pH', url: 'https://pubs.usgs.gov/twri/twri9a6/twri9a64/twri9a_6.4_ver2.0.pdf' },
      { label: 'USGS: Corrosivity', url: 'https://www.usgs.gov/mission-areas/water-resources/science/corrosivity' },
      { label: 'CDC: Water intoxication', url: 'https://www.cdc.gov/mmwr/preview/mmwrhtml/00032470.htm' },
      hydrogenBonds,
    ],
  },
  {
    cid: 297,
    overview: 'The simplest alkane and a major component of natural gas.',
    uses: 'Natural-gas fuel; chemical feedstock.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Low in water',
      flammability: 'Extremely flammable gas',
      reactivity: 'Relatively unreactive; incompatible with strong oxidizers',
      toxicity: 'High concentrations displace oxygen; suffocation risk',
      acidity: 'N/A for dry gas',
      oxidation: 'Oxidized during combustion',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [icsc('Methane', '0291'), alkanes],
  },
  {
    cid: 280,
    overview: 'A gas in air and fizzy drinks; its solid form is dry ice.',
    uses: 'Carbonated drinks; dry ice; some fire extinguishers.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Slightly soluble in water; depends on temperature and pressure',
      flammability: 'Nonflammable',
      reactivity: 'Reacts with alkaline compounds and reactive metals',
      toxicity: 'High concentrations impair body functions; suffocation risk',
      acidity: 'Acidifies water when dissolved; pH depends on conditions',
      oxidation: 'Carbon already highly oxidized',
      combustion: 'Noncombustible; common combustion product',
    },
    sources: [
      icsc('Carbon dioxide', '0021'),
      { label: 'USGS: pH and water', url: 'https://www.usgs.gov/water-science-school/science/ph-and-water' },
    ],
  },
  {
    cid: 702,
    overview: 'A two-carbon alcohol with a polar hydroxyl group.',
    uses: 'Solvents; fuels; beverages; sanitizer formulations.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Miscible with water',
      functionalGroups: 'Primary alcohol (–OH)',
      hydrogenBonding: 'Donor and acceptor',
      flammability: 'Highly flammable liquid and vapour',
      reactivity: 'Alcohol reactions; incompatible with strong oxidizers',
      toxicity: 'Eye irritant; nervous-system effects; repeated ingestion damages organs',
      acidity: 'Weak acid/base behaviour; no fixed aqueous pH',
      oxidation: 'Can form ethanal, then ethanoic acid, depending on conditions',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [icsc('Ethanol', '0044'), alcohols, functionalGroups, hydrogenBonds],
  },
  {
    cid: 5793,
    overview: 'An energy-source carbohydrate, mainly present as ring forms in water.',
    uses: 'Foods; cellular energy source.',
    properties: {
      state: 'Solid (25°C, 1 atm)',
      appearance: 'White powder',
      solubility: 'Soluble in water',
      functionalGroups: 'Hydroxyl groups; cyclic hemiacetal in the displayed form',
      flammability: 'Combustible solid; fine dust can explode',
      reactivity: 'Reducing sugar; reacts with suitable oxidizers',
      toxicity: 'Not reviewed',
      acidity: 'No fixed pH for dry solid',
      oxidation: 'Open-chain aldehyde can oxidize to a carboxylic-acid group',
      combustion: 'Releases energy; complete combustion forms CO₂ + H₂O',
    },
    sources: [
      icsc('Glucose', '0865'),
      { label: 'UCLA: Reducing sugars', url: 'https://www.chem.ucla.edu/~harding/IGOC/R/reducing_sugar.html' },
      { label: 'PubChem: Glucose structure', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/5793' },
      functionalGroups,
    ],
  },
  {
    cid: 2519,
    overview: 'A nitrogen-containing stimulant found in coffee and tea.',
    uses: 'Coffee; tea; stimulant-containing products.',
    properties: {
      state: 'Solid (25°C, 1 atm)',
      appearance: 'White crystals or powder',
      flammability: 'Combustible solid',
      reactivity: 'Decomposes on burning',
      toxicity: 'Nervous-system and cardiovascular effects; excessive exposure harmful',
      acidity: 'Roughly neutral aqueous solutions; formulation dependent',
      oxidation: 'Burning can produce nitrogen oxides',
      combustion: 'Burns with irritating or toxic fumes',
      stability: 'Sublimes on heating; decomposes on burning',
    },
    sources: [
      icsc('Caffeine', '0405'),
      { label: 'PubChem: Caffeine', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/Caffeine' },
      { label: 'USP: Caffeine solutions', url: 'https://doi.usp.org/USPFCC/FCC_F100913_06_01.html' },
    ],
  },
  {
    cid: 977,
    overview: 'A diatomic gas involved in respiration, oxidation, and combustion.',
    uses: 'Respiration; medical oxygen; industrial oxidation.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      solubility: 'Low in water',
      flammability: 'Nonflammable; supports burning of other substances',
      reactivity: 'Strong oxidizer; reacts with fuels and reducing materials',
      toxicity: 'Very high or prolonged elevated exposure can damage tissues',
      acidity: 'N/A for dry gas',
      oxidation: 'Oxidizer; contributes to metal corrosion with moisture',
      combustion: 'Oxidizing partner, not the fuel',
    },
    sources: [
      icsc('Oxygen', '0138'),
      { label: 'USGS: Corrosivity', url: 'https://www.usgs.gov/mission-areas/water-resources/science/corrosivity' },
    ],
  },
  {
    cid: 222,
    overview: 'A nitrogen compound that accepts protons to form ammonium.',
    uses: 'Fertilizer production; cleaning formulations; refrigerant.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: '54 g/100 mL water at 20°C',
      hydrogenBonding: 'Donor and acceptor',
      flammability: 'Flammable gas',
      reactivity: 'Reacts vigorously with acids, halogens, and strong oxidizers',
      toxicity: 'Toxic by inhalation; corrosive to skin, eyes, and airways',
      acidity: 'Weak base in water; pH depends on concentration',
      oxidation: 'Reacts with oxidizers; attacks copper and some other metals',
      combustion: 'Can burn; nitrogen-containing products depend on conditions',
    },
    sources: [
      icsc('Ammonia', '0414'),
      { label: 'ATSDR: Ammonia chemistry', url: 'https://www.ncbi.nlm.nih.gov/books/NBK598719/' },
      hydrogenBonds,
    ],
  },
  {
    cid: 784,
    overview: 'An oxidizer with concentration-dependent properties and hazards.',
    uses: 'Bleaching; disinfectant formulations.',
    properties: {
      solubility: 'Miscible with water',
      functionalGroups: 'Peroxide (O–O)',
      flammability: 'Noncombustible; concentrated solutions can intensify fires',
      reactivity: 'Decomposes into water and oxygen',
      toxicity: 'Concentration-dependent; concentrated solutions cause severe burns',
      acidity: 'Solution pH depends on concentration and formulation',
      oxidation: 'Oxidizes many organic substances; bleaching action',
      combustion: 'Decomposition releases heat and oxygen; not ordinary fuel combustion',
      stability: 'Light, heat, and metal catalysts accelerate decomposition',
    },
    sources: [
      icsc('Concentrated hydrogen peroxide', '0164'),
      { label: 'PubChem / ATSDR: Hydrogen peroxide', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/hydrogenperoxide' },
    ],
  },
  {
    cid: 887,
    overview: 'The simplest alcohol; toxic despite its resemblance to ethanol.',
    uses: 'Solvent; fuel; chemical feedstock.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Miscible with water',
      functionalGroups: 'Alcohol (–OH)',
      flammability: 'Highly flammable liquid and vapour',
      reactivity: 'Reacts with strong oxidizers, acids, and reducing agents',
      toxicity: 'Toxic; exposure can cause blindness or death',
      acidity: 'Weak acid/base behaviour; no fixed aqueous pH',
      oxidation: 'Can form methanal; further oxidation depends on conditions',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [icsc('Methanol', '0057'), alcohols, functionalGroups],
  },
  {
    cid: 6324,
    overview: 'A two-carbon alkane found in natural gas.',
    uses: 'Natural gas; ethene production.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Very low in water',
      flammability: 'Extremely flammable gas',
      reactivity: 'Reacts with halogens and strong oxidizers',
      toxicity: 'High concentrations displace oxygen; suffocation risk',
      acidity: 'N/A for dry gas',
      oxidation: 'Oxidized during combustion',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [
      icsc('Ethane', '0266'),
      alkanes,
      { label: 'PubChem: Ethane uses', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/Ethane' },
    ],
  },
  {
    cid: 8252,
    overview: 'A three-carbon alkene whose double bond enables addition reactions.',
    uses: 'Polypropylene plastics; chemical feedstock.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Low in water',
      functionalGroups: 'Alkene (C=C)',
      flammability: 'Extremely flammable gas',
      reactivity: 'Addition and polymerization; conditions determine products',
      toxicity: 'High concentrations: drowsiness and suffocation risk',
      acidity: 'N/A for dry gas',
      oxidation: 'Reacts with strong oxidizers',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [
      icsc('Propene', '0559'),
      { label: 'NOAA: Unsaturated hydrocarbons', url: 'https://cameochemicals.noaa.gov/react/28' },
      { label: 'PubChem: Propene uses', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/propylene' },
      functionalGroups,
    ],
  },
  {
    cid: 180,
    overview: 'A small ketone with a polar carbonyl group.',
    uses: 'Solvents; nail-polish removers.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Miscible with water',
      functionalGroups: 'Ketone (C=O)',
      flammability: 'Highly flammable liquid and vapour',
      reactivity: 'Carbonyl reactions; incompatible with strong oxidizers',
      toxicity: 'Eye/airway irritant; high vapour exposure impairs consciousness',
      acidity: 'No fixed aqueous pH for neat liquid',
      oxidation: 'Dangerous reactions with strong oxidizers',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [
      icsc('Acetone', '0087'),
      { label: 'NOAA: Ketones', url: 'https://cameochemicals.noaa.gov/react/19' },
      { label: 'PubChem: Acetone uses', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/Acetone' },
      functionalGroups,
    ],
  },
  {
    cid: 3776,
    overview: 'A secondary alcohol also called isopropyl alcohol.',
    uses: 'Solvents; cleaning and disinfectant formulations.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Miscible with water',
      functionalGroups: 'Secondary alcohol (–OH)',
      flammability: 'Highly flammable liquid and vapour',
      reactivity: 'Alcohol reactions; incompatible with strong oxidizers',
      toxicity: 'Eye/airway irritant; nervous-system effects at high exposure',
      acidity: 'Weak acid/base behaviour; no fixed aqueous pH',
      oxidation: 'Can form acetone',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
      stability: 'Heating can cause decomposition',
    },
    sources: [icsc('2-Propanol', '0554'), alcohols, functionalGroups],
  },
  {
    cid: 8857,
    overview: 'An ester also called ethyl acetate.',
    uses: 'Solvents; coatings; adhesives.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: '8.7 g/100 mL water at 20°C',
      functionalGroups: 'Ester (–COO–)',
      flammability: 'Highly flammable liquid and vapour',
      reactivity: 'Hydrolysis; vigorous reactions with strong acids or bases',
      toxicity: 'Eye/airway irritant; high vapour exposure impairs consciousness',
      acidity: 'No fixed aqueous pH for neat liquid',
      oxidation: 'Incompatible with strong oxidizers',
      combustion: 'Complete combustion: CO₂ + H₂O; releases heat',
    },
    sources: [
      icsc('Ethyl ethanoate', '0367'),
      { label: 'NOAA: Esters', url: 'https://cameochemicals.noaa.gov/react/13' },
      { label: 'NASA: Ethyl acetate', url: 'https://ntrs.nasa.gov/api/citations/20210022592/downloads/Ethyl%20Acetate%20Full%20SMAC%20EXPORT.pdf' },
      functionalGroups,
    ],
  },
  {
    cid: 176,
    overview: 'The acid in vinegar; concentrated acid has different hazards from vinegar.',
    uses: 'Vinegar; chemical manufacturing.',
    properties: {
      state: 'Liquid (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: 'Miscible with water',
      functionalGroups: 'Carboxylic acid (–COOH)',
      flammability: 'Concentrated acid is flammable',
      reactivity: 'Neutralizes bases; ester formation under suitable conditions',
      toxicity: 'Concentrated acid is corrosive to skin, eyes, and airways',
      acidity: 'Weak acid in water; pH depends on concentration',
      oxidation: 'Incompatible with strong oxidizers',
      combustion: 'Concentrated acid burns; releases heat',
    },
    sources: [icsc('Ethanoic acid', '0363'), alcohols, functionalGroups],
  },
  {
    cid: 8254,
    overview: 'An ether isomer of ethanol: same formula, different atom connections.',
    uses: 'Aerosol propellant; chemical feedstock.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      functionalGroups: 'Ether (C–O–C)',
      hydrogenBonding: 'Acceptor; no O–H hydrogen-bond donor',
      flammability: 'Extremely flammable gas',
      reactivity: 'Reacts with oxidizers',
      toxicity: 'High exposure impairs consciousness; suffocation risk',
      acidity: 'Weak Lewis base; N/A for dry-gas pH',
      oxidation: 'Can form peroxides in air and light',
      combustion: 'Burns with irritating fumes',
      stability: 'May form explosive peroxides in air/light',
    },
    sources: [
      icsc('Dimethyl ether', '0454'),
      { label: 'NOAA: Ethers', url: 'https://cameochemicals.noaa.gov/react/14' },
      { label: 'Health Canada: Dimethyl ether use', url: 'https://webprod.hc-sc.gc.ca/nhpid-bdipsn/ingredReq?id=11451&wbdisable=true' },
      functionalGroups,
      hydrogenBonds,
    ],
  },
  {
    cid: 6323,
    overview: 'A methyl halide used as a simple substitution-reaction teaching example.',
    uses: 'Substitution-reaction teaching model.',
    properties: {
      state: 'Gas (25°C, 1 atm)',
      appearance: 'Colourless',
      solubility: '1.5 g/100 mL water at 20°C',
      functionalGroups: 'Haloalkane (C–Br)',
      flammability: 'Combustible under specific conditions',
      reactivity: 'Reacts with oxidizers; attacks many metals when moist',
      toxicity: 'Toxic by inhalation; delayed organ damage possible',
      acidity: 'N/A for dry gas',
      oxidation: 'Incompatible with strong oxidizers',
      combustion: 'Burning/decomposition produces toxic, corrosive fumes',
      stability: 'Decomposes on heating',
    },
    sources: [icsc('Bromomethane', '0109'), functionalGroups],
  },
  {
    cid: 5234,
    overview: 'An ionic solid of sodium and chloride ions, not a discrete covalent molecule.',
    uses: 'Table salt; food seasoning and preservation.',
    properties: {
      state: 'Solid (25°C, 1 atm)',
      appearance: 'Colourless crystals or white powder',
      solubility: '36.0 g/100 g water at 25°C',
      flammability: 'Nonflammable',
      reactivity: 'Dissolves into sodium and chloride ions',
      toxicity: 'Excess intake disturbs salt–water balance; dust may irritate eyes',
      acidity: 'Near-neutral aqueous solutions; measured pH depends on formulation',
      oxidation: 'Dissolved chloride can accelerate metal corrosion',
      combustion: 'Noncombustible',
    },
    sources: [
      { label: 'PubChem: Sodium chloride', url: 'https://pubchem.ncbi.nlm.nih.gov/compound/Sodium_chloride' },
      { label: 'FDA: Sodium in your diet', url: 'https://www.fda.gov/food/nutrition-education-resources-materials/sodium-your-diet' },
      { label: 'NOAA: Non-redox-active inorganic compounds', url: 'https://cameochemicals.noaa.gov/react/46' },
      { label: 'USGS: Corrosivity', url: 'https://www.usgs.gov/mission-areas/water-resources/science/corrosivity' },
    ],
  },
  {
    cid: 14798,
    overview: 'An ionic, strongly caustic compound that supplies hydroxide ions in water.',
    uses: 'Soap manufacturing; cleaning formulations; chemical processing.',
    properties: {
      state: 'Solid (25°C, 1 atm)',
      appearance: 'White solid',
      solubility: '109 g/100 mL water at 20°C; dissolution releases heat',
      flammability: 'Nonflammable; incompatible reactions may create fire hazards',
      reactivity: 'Vigorous acid reactions; some metals release hydrogen',
      toxicity: 'Severely corrosive to skin, eyes, and respiratory tissue',
      acidity: 'Strong base in water; pH depends on concentration',
      oxidation: 'Corrodes some metals; not an ordinary oxidizer',
      combustion: 'Noncombustible; dissolution and neutralization can release heat',
      stability: 'Hygroscopic: absorbs moisture from air',
    },
    sources: [
      icsc('Sodium hydroxide', '0360'),
      { label: 'USDA: Sodium hydroxide uses', url: 'https://www.ams.usda.gov/sites/default/files/media/SodiumHydroxideTR_05082020.pdf' },
    ],
  },
];

const profilesByCid = new Map(chemicalProfiles.map((profile) => [profile.cid, profile]));

export function chemicalProfileForCid(cid: number): ChemicalProfile | undefined {
  return profilesByCid.get(cid);
}
