"""Site-specific alcohol/hypochlorite net oxidation, not a reagent protocol.

One selected primary/secondary alcohol loses its O–H and one C–H to the
oxidant oxygen. Other eligible alcohols are alternative sites, not a promise
of selective mono-oxidation; aldehyde isolation is never inferred.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols"
CONDITIONS_SOURCE = "https://www.orgsyn.org/demo.aspx?prep=CV8P0367"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")


def sites(molecule):
    return graph.find_alcohols(molecule)


def classification(molecule, site):
    degree = graph.substitution_degree(molecule.GetAtomWithIdx(site[0]))
    return "primary" if degree <= 1 else "secondary" if degree == 2 else "tertiary"


def alcohol_issue(molecule, site, *, selected=False):
    if tuple(site) not in sites(molecule):
        return "The selected site is not a neutral saturated alcohol C–OH; phenols, acids and ethers are not alcohol oxidation sites."
    carbon, oxygen = (molecule.GetAtomWithIdx(i) for i in site)
    if (oxygen.GetDegree() != 1 + sum(n.GetAtomicNum() == 1 for n in oxygen.GetNeighbors())
            or molecule.GetBondBetweenAtoms(*site).GetBondType() != Chem.BondType.SINGLE
            or any(n.GetAtomicNum() not in {1, 6, 8} for n in carbon.GetNeighbors())
            or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1):
        return "Geminal-diol/hemiacetal or nonordinary alcohol environments need separate oxidation/cleavage validation."
    if selected and (classification(molecule, site) == "tertiary" or not graph.attached_hydrogens(carbon)):
        return "Tertiary alcohols lack the carbon-bound H required by ordinary alcohol-to-carbonyl oxidation; no C–C cleavage is invented."
    return None


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def site_check(molecule, site):
    return alcohol_issue(molecule, site, selected=True)


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "alcohol":
        other = next((s for s in sites(molecule) if set(s) == set(indices)), None)
        issue = alcohol_issue(molecule, other) if other else "This OH is not an ordinary saturated alcohol."
        if issue:
            return "rejected", "unvalidated", issue
        if set(other) == set(site):
            return "reactive", "validated", f"Selected {classification(molecule, site)} alcohol: C–O becomes C=O; its O–H and one carbon-bound H form water with the oxidant oxygen."
        separation = distance(molecule, site[0], other[0])
        if separation <= 1:
            return "rejected", "competition", "Vicinal/geminal alcohol sites can involve oxidative cleavage or coupled chemistry; this hypochlorite one-site model does not validate that environment."
        ring_size = distance(molecule, other[1], site[0]) + 1
        if ring_size in {5, 6}:
            return "rejected", "competition", f"Oxidation can give a hydroxy carbonyl with a potential {ring_size}-membered hemiacetal/hemiketal closure and further oxidation; cyclization/lactonization is not modeled."
        if classification(molecule, other) == "tertiary":
            return "preserved", "bounded", "This separate tertiary OH has no carbon-bound H for ordinary carbonyl formation and is retained in the net edit; acid-induced cleavage/dehydration is not predicted."
        return "alternative-site", "bounded", "Another separated primary/secondary alcohol is independently oxidizable and stays unchanged in this one-site net option. Relative rates, selective mono-oxidation and complete conversion are not predicted."
    if kind == "ether":
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None or oxygen.GetDegree() != 2:
            return "rejected", "unvalidated", "This ether lacks an ordinary neutral two-carbon oxygen environment."
        for carbon in oxygen.GetNeighbors():
            if (carbon.GetAtomicNum() != 6 or molecule.GetBondBetweenAtoms(carbon.GetIdx(), oxygen.GetIdx()).GetBondType() != Chem.BondType.SINGLE
                    or (not carbon.GetIsAromatic() and carbon.GetHybridization() != Chem.HybridizationType.SP3)):
                return "rejected", "competition", "Enol/unsaturated or nonordinary ether oxidation is not screened by this alcohol rule."
            if sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1:
                return "rejected", "unvalidated", "Acetal/ketal and multiple-oxygen carbon environments require separate hydrolysis/oxidation validation."
            if not carbon.GetIsAromatic() and graph.is_allylic_or_benzylic(carbon):
                return "rejected", "unvalidated", "Benzyl/allyl ether retention under this oxidant has not been validated; distance alone does not prove it inert."
        if all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Diaryl ether compatibility is outside this increment's screened ether set."
        return "preserved", "bounded", "This screened saturated dialkyl or carbocyclic aryl–alkyl ether keeps its C–O bonds in the net edit. Oxidative ether cleavage and condition-specific stability are not experimentally predicted."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic compatibility with this oxidant needs a separate policy."
        return "preserved", "bounded", "The carbocyclic aromatic skeleton stays unchanged in the alcohol-to-carbonyl net option; aromatic chlorination/side reactions are not excluded experimentally."
    if kind in {"alkene", "alkyne"}:
        return "rejected", "competition", f"An additional {kind} can undergo oxidant addition/side reactions; selective alcohol oxidation with its geometry preserved is not validated."
    if kind == "aldehyde":
        return "rejected", "competition", "An existing aldehyde can undergo further oxidation; leaving it unchanged while oxidizing this alcohol needs separate chemoselectivity validation."
    if kind in {"ketone", "carbonyl"}:
        return "rejected", "competition", "Additional carbonyl halogenation/cleavage or coupled hydroxy-carbonyl chemistry is not validated by this alcohol oxidation policy."
    return "rejected", "unvalidated", f"The additional {kind} group has no validated compatibility policy for alcohol oxidation; unsupported does not mean chemically incapable of oxidation."


def additional_check(molecule, site):
    for atom in molecule.GetAtoms():
        if atom.GetIdx() != site[0] and atom.GetChiralTag() in stereo.TETRAHEDRAL and distance(molecule, atom.GetIdx(), site[0]) <= 1:
            yield ("near-site-stereo", "unvalidated", f"Specified center at substrate atom {atom.GetIdx() + 1} is adjacent to the new carbonyl; possible epimerization is not covered by distant-center retention.", [atom.GetIdx()])


POLICY = compatibility.SitePolicy("alcohol/hypochlorite oxidation", frozenset({"C", "H", "O"}),
                                  site_check, group_check, additional_check, added_atoms=-2,
                                  extra_groups=(("ether", ETHER_QUERY),))


def assess(molecule, site):
    return compatibility.assess_site(molecule, site, POLICY)


def oxidant_atoms(reagent):
    fragments = Chem.GetMolFrags(reagent, asMols=True)
    anions = [f for f in fragments if f.GetNumAtoms() == 2 and f.GetNumBonds() == 1
              and sorted((a.GetSymbol(), a.GetFormalCharge()) for a in f.GetAtoms()) == [("Cl", 0), ("O", -1)]
              and f.GetBondWithIdx(0).GetBondType() == Chem.BondType.SINGLE]
    cations = [f for f in fragments if f.GetNumAtoms() == 1 and f.GetAtomWithIdx(0).GetSymbol() in {"Li", "Na", "K", "Rb", "Cs"}
               and f.GetAtomWithIdx(0).GetFormalCharge() == 1]
    if (len(fragments) != 2 or len(anions) != 1 or len(cations) != 1
            or any(a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in reagent.GetAtoms())):
        raise ValueError("This oxidation consumes one actual alkali-metal hypochlorite formula unit; arbitrary oxidants or counterions are not substituted.")
    return next(a for a in reagent.GetAtoms() if a.GetSymbol() == "O"), next(a for a in reagent.GetAtoms() if a.GetSymbol() == "Cl")


def edit_contract(substrate, reagent, site):
    carbon, oxygen = (substrate.GetAtomWithIdx(i) for i in site)
    hs = [next(n.GetAtomMapNum() for n in atom.GetNeighbors() if n.GetAtomicNum() == 1) for atom in (carbon, oxygen)]
    ends = [carbon.GetAtomMapNum(), oxygen.GetAtomMapNum()]
    oxidant_o, chlorine = (a.GetAtomMapNum() for a in oxidant_atoms(reagent))
    return [{"atomMaps": ends, "before": 1.0, "after": 2.0},
            *[{"atomMaps": [end, h], "before": 1.0, "after": None} for end, h in zip(ends, hs)],
            {"atomMaps": [oxidant_o, chlorine], "before": 1.0, "after": None},
            *[{"atomMaps": [oxidant_o, h], "before": None, "after": 1.0} for h in hs]]


def charge_contract(reagent):
    oxygen, chlorine = oxidant_atoms(reagent)
    return [{"atomMap": oxygen.GetAtomMapNum(), "before": -1, "after": 0},
            {"atomMap": chlorine.GetAtomMapNum(), "before": 0, "after": -1}]


def consumed_centers(substrate, site):
    carbon = substrate.GetAtomWithIdx(site[0])
    return [carbon.GetAtomMapNum()] if carbon.GetChiralTag() in stereo.TETRAHEDRAL else []


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    compatibility.validate_edit_contract(before, after, edit_contract(substrate, reagent, site),
                                        charge_changes=charge_contract(reagent), consumed_tetrahedral_centers=consumed_centers(substrate, site),
                                        expected_fragments=4)
