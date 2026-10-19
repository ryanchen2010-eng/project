import type { Molecule } from './molecules';
import type { Reactant } from './reactant-entry';
import type { SolutionCompound } from './solution-calculator-panel';

/** Only an explicit, complete g/mol value is eligible for an automatic mass. */
export function parseMolarMass(value: string): number | undefined {
  const match = /^\s*(\d+(?:\.\d+)?|\.\d+)\s+g\/mol\s*$/.exec(value);
  if (!match) return undefined;
  const mass = Number(match[1]);
  return Number.isFinite(mass) && mass > 0 ? mass : undefined;
}

export function solutionCompoundFromMolecule(molecule: Molecule): SolutionCompound {
  return { id: molecule.id, name: molecule.name, formula: molecule.formula,
    molarMass: parseMolarMass(molecule.properties.mass) };
}

/** A formula alone cannot distinguish isomers, ions, or salts. */
export function solutionCompoundForReactant(reactant: Reactant | undefined, records: Molecule[]): SolutionCompound | undefined {
  if (!reactant) return undefined;
  const reviewed = records.find((record) => record.id === reactant.id && record.structureForm === reactant.smiles);
  return { id: `${reactant.id}:${reactant.smiles}`, name: reviewed?.name ?? reactant.name, formula: reviewed?.formula ?? reactant.formula,
    molarMass: reviewed ? parseMolarMass(reviewed.properties.mass) : undefined };
}
