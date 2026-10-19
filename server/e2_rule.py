"""Hydroxide E2: one acyclic alpha/beta site, exact edits and bounded anti stereo.

These are independently selectable net pathways, never product ratios or proof
of experimental conversion. Cyclic elimination, new bases and unvalidated
spectators do not inherit permission from substitution or hydrogenation.
"""
from functools import lru_cache
from copy import deepcopy
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo

SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect"
RING_SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-9-the-e2-reaction-and-cyclohexane-conformation"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")
NONALKYL_HALIDE = Chem.MolFromSmarts("[#6;!X4]-[F,Cl,Br,I]")


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def halide_issue(molecule, halide):
    if tuple(halide) not in graph.find_alkyl_halides(molecule):
        return "E2 requires an actual single C(sp³)–Cl/Br/I bond; other leaving-group families are not enabled."
    carbon, leaving = (molecule.GetAtomWithIdx(i) for i in halide)
    if carbon.IsInRing():
        return "Ring-bound E2 requires separately validated ring conformations/trans-diaxial geometry; it is not enabled by this acyclic increment."
    if any(n.GetAtomicNum() not in {1, 6} for n in carbon.GetNeighbors() if n.GetIdx() != leaving.GetIdx()):
        return "Geminal halide or heteroatom-substituted electrophiles need a separate E2/competing-chemistry policy."
    if graph.is_allylic_or_benzylic(carbon) and not any(n.GetIsAromatic() for n in graph.carbon_neighbors(carbon)):
        return "Allylic/propargylic or conjugated elimination environments are not generalized by this increment."
    return None


def beta_issue(molecule, halide, beta):
    alpha = halide[0]
    atom = molecule.GetAtomWithIdx(beta)
    bond = molecule.GetBondBetweenAtoms(alpha, beta)
    if (bond is None or bond.GetBondType() != Chem.BondType.SINGLE or atom.GetAtomicNum() != 6
            or atom.GetHybridization() != Chem.HybridizationType.SP3 or not graph.attached_hydrogens(atom)):
        return "The selected beta carbon must be sp³, single-bonded to alpha and bear an actual C–H bond."
    if atom.IsInRing() or bond.IsInRing():
        return "Ring-bound beta-H elimination and exocyclic ring products require their own conformational validation."
    if any(n.GetAtomicNum() not in {1, 6} for n in atom.GetNeighbors()):
        return "A heteroatom/halide on the selected beta carbon can give unvalidated enol/vinyl or coupled elimination chemistry."
    return None


def sites(molecule):
    work = Chem.Mol(molecule)
    for atom in work.GetAtoms():
        atom.SetAtomMapNum(0)  # Provenance labels must not split equivalent beta sites.
    ranks = list(Chem.CanonicalRankAtoms(work, breakTies=False))
    result = []
    for alpha, leaving in graph.find_alkyl_halides(molecule):
        seen = set()
        for beta in graph.beta_hydrogens(molecule, alpha):
            if ranks[beta] not in seen:
                result.append((alpha, leaving, beta)); seen.add(ranks[beta])
    return result


def site_check(molecule, site):
    return halide_issue(molecule, site)


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "haloalkane":
        other = next((s for s in graph.find_alkyl_halides(molecule) if set(s) == set(indices)), None)
        issue = halide_issue(molecule, other) if other else "This halide has no validated ordinary E2 environment."
        if issue:
            return "rejected", "unvalidated", issue
        if set(other) == set(site):
            return "reactive", "validated", "Selected C–X departs as an actual beta C–H forms C=C in one concerted hydroxide elimination."
        if distance(molecule, site[0], other[0]) <= 1:
            return "rejected", "competition", "Adjacent multiple halides can give coupled or vinyl-halide elimination; this spectator policy is not validated."
        return "alternative-site", "bounded", "Another separated alkyl halide stays unchanged in this one-site net option. Subsequent elimination/substitution and selective mono-conversion are not predicted."
    if kind == "alcohol":
        other = next((s for s in graph.find_alcohols(molecule) if set(s) == set(indices)), None)
        if other is None or sum(n.GetAtomicNum() == 8 for n in molecule.GetAtomWithIdx(other[0]).GetNeighbors()) != 1:
            return "rejected", "unvalidated", "Only ordinary saturated remote OH groups are screened; hemiacetals/geminal O require separate validation."
        for alpha, _ in graph.find_alkyl_halides(molecule):
            issue = compatibility.oxygen_closure_issue(molecule, other[1], alpha, "E2")
            if issue:
                return "rejected", *issue
        return "preserved", "bounded", "Screened remote OH bonds remain unchanged in this net elimination. Proton equilibria, intermolecular ether formation and larger-ring cyclization are not excluded experimentally."
    if kind == "ether":
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None or oxygen.GetDegree() != 2 or distance(molecule, oxygen.GetIdx(), site[0]) < 3:
            return "rejected", "unvalidated", "An ether near alpha needs separate neighboring-group/E2 validation; this policy screens remote ethers only."
        if all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Diaryl ether base compatibility is not generalized here."
        for carbon in oxygen.GetNeighbors():
            if (carbon.GetAtomicNum() != 6 or (not carbon.GetIsAromatic() and carbon.GetHybridization() != Chem.HybridizationType.SP3)
                    or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1):
                return "rejected", "unvalidated", "Unsaturated/enol, acetal/ketal or nonordinary ethers need their own E2/base policy."
        return "preserved", "bounded", "The remote dialkyl/carbocyclic aryl–alkyl ether retains its bonds. No ether cleavage, neighboring participation or experimental inertness is asserted."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic base/elimination compatibility is unvalidated."
        return "preserved", "bounded", "The carbocyclic aromatic skeleton stays unchanged, including bounded benzylic elimination options; selectivity and competing pathways are not predicted."
    if kind in {"alkene", "alkyne"}:
        return "rejected", "unvalidated", "Existing unsaturation/conjugation is not validated as an E2 spectator; allylic and further elimination chemistry is not silently enabled."
    return "rejected", "unvalidated", f"The additional {kind} has no validated hydroxide/E2 compatibility policy; unsupported does not mean chemically incapable of elimination."


POLICY = compatibility.SitePolicy("hydroxide E2 elimination", frozenset({"C", "H", "O", "Cl", "Br", "I"}),
                                  site_check, group_check, lambda molecule, site: (), added_atoms=-2,
                                  extra_groups=(("ether", ETHER_QUERY), ("non-alkyl halide", NONALKYL_HALIDE)))


def assess(molecule, site):
    if len(site) != 3 or len(set(site)) != 3 or any(type(i) is not int or not 0 <= i < molecule.GetNumAtoms() for i in site):
        return {"version": 1, "policy": POLICY.name, "siteAtoms": list(site), "groups": [], "eligible": False,
                "rejections": [{"code": "invalid-site", "category": "structural", "message": "Select distinct alpha carbon, leaving atom and beta carbon.", "atomIndices": list(site)}]}
    report = compatibility.assess_site(molecule, site[:2], POLICY)
    report["siteAtoms"] = list(site)
    issue = beta_issue(molecule, site[:2], site[2])
    if issue:
        report["rejections"].append({"code": "beta-environment", "category": "unvalidated", "message": issue, "atomIndices": [site[2]]})
        report["eligible"] = False
    return report


def participants(substrate, reagent, site):
    # Explicit reaction species carry all actual H maps. No H is invented or
    # selected by atom name. CH2/CH3 sites use one representative net H map;
    # stereochemical equivalence or distinct E/Z populations are not inferred.
    alpha, leaving, beta = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in site]
    hydrogens = sorted(n.GetAtomMapNum() for n in substrate.GetAtomWithIdx(site[2]).GetNeighbors() if n.GetAtomicNum() == 1)
    oxygens = [a for a in reagent.GetAtoms() if a.GetAtomicNum() == 8]
    if (reagent.GetNumAtoms() != 2 or reagent.GetNumBonds() != 1 or len(oxygens) != 1
            or oxygens[0].GetFormalCharge() != -1 or graph.attached_hydrogens(oxygens[0]) != 1
            or reagent.GetBondWithIdx(0).GetBondType() != Chem.BondType.SINGLE
            or any(a.GetAtomicNum() not in {1, 8} or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery()
                   or (a.GetAtomicNum() == 1 and a.GetFormalCharge()) for a in reagent.GetAtoms())):
        raise ValueError("This E2 uses one actual OH⁻ ion; water, alkoxides and other bases are not substituted by name.")
    if not hydrogens:
        raise ValueError("No actual mapped beta C–H is available for elimination.")
    return {"alpha": alpha, "leaving": leaving, "beta": beta, "hydrogen": hydrogens[0], "base": oxygens[0].GetAtomMapNum()}


def edit_contract(substrate, reagent, site):
    s = participants(substrate, reagent, site)
    return [{"atomMaps": [s["alpha"], s["leaving"]], "before": 1.0, "after": None},
            {"atomMaps": [s["beta"], s["hydrogen"]], "before": 1.0, "after": None},
            {"atomMaps": [s["alpha"], s["beta"]], "before": 1.0, "after": 2.0},
            {"atomMaps": [s["base"], s["hydrogen"]], "before": None, "after": 1.0}]


def charge_contract(substrate, reagent, site):
    s = participants(substrate, reagent, site)
    return [{"atomMap": s["base"], "before": -1, "after": 0}, {"atomMap": s["leaving"], "before": 0, "after": -1}]


def apply_stereo(before, editor, s):
    atoms = {a.GetAtomMapNum(): a for a in editor.GetAtoms()}
    for m in (s["alpha"], s["beta"]):
        atoms[m].SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    bond = editor.GetBondBetweenAtoms(atoms[s["alpha"]].GetIdx(), atoms[s["beta"]].GetIdx())
    expected = stereo.e2_anti_stereo(before, s)
    bond.SetStereo(Chem.BondStereo.STEREONONE)
    if expected:
        refs = expected["referenceMaps"]
        if bond.GetBeginAtom().GetAtomMapNum() != s["alpha"]:
            refs = list(reversed(refs))
        bond.SetStereoAtoms(*(atoms[m].GetIdx() for m in refs))
        bond.SetStereo(Chem.BondStereo.STEREOCIS if expected["sameSide"] else Chem.BondStereo.STEREOTRANS)
        Chem.SetDoubleBondNeighborDirections(editor)


def validate(before, after, substrate, reagent, site):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    compatibility.validate_edit_contract(before, after, edit_contract(substrate, reagent, site),
                                        charge_changes=charge_contract(substrate, reagent, site),
                                        eliminations=[participants(substrate, reagent, site)], expected_fragments=3)


def check_conformations(molecule, hydrogen, beta, alpha, leaving):
    """Measure supplied conformation, then construct anti by one acyclic rotation.

No unfavorable single conformer is a rejection. The rotated candidate is
kinematic, not relaxed, clash-cleared, an energy minimum or a transition state.
"""
    measured = stereo.anti_periplanar(molecule, hydrogen, beta, alpha, leaving)
    atoms = {a.GetAtomMapNum(): a for a in molecule.GetAtoms()}
    if any(atoms[m].IsInRing() for m in (alpha, beta)) or molecule.GetBondBetweenAtoms(atoms[alpha].GetIdx(), atoms[beta].GetIdx()).IsInRing():
        raise ValueError("Acyclic rotation cannot validate cyclic E2 geometry.")
    rotated = Chem.Mol(molecule)
    rdMolTransforms.SetDihedralDeg(rotated.GetConformer(), *(atoms[m].GetIdx() for m in (hydrogen, beta, alpha, leaving)), 180.0)
    candidate = stereo.anti_periplanar(rotated, hydrogen, beta, alpha, leaving)
    # Rotation is rigid on either side of the acyclic bond: independently
    # ensure its measured 3D configurations still match all specified tags.
    measured_stereo = Chem.Mol(rotated)
    Chem.AssignAtomChiralTagsFromStructure(measured_stereo, replaceExistingTags=True)
    for old, new in zip(rotated.GetAtoms(), measured_stereo.GetAtoms()):
        if old.GetChiralTag() in stereo.TETRAHEDRAL and stereo._tetra_signature(old)[1] != stereo._tetra_signature(new)[1]:
            raise ValueError("The anti candidate did not preserve a specified 3D configuration.")
    return {"sampledConformer": measured, "antiCandidate": candidate,
            "status": "anti candidate constructed" if candidate["antiPeriplanar"] else "unresolved",
            "note": "One acyclic bond rotation, not an energy/clash search, transition state, E/Z population or rate prediction. A sampled non-anti conformer does not prove E2 impossible."}


@lru_cache(maxsize=256)
def _geometry(mapped_smiles, hydrogen, beta, alpha, leaving):
    params = Chem.SmilesParserParams(); params.removeHs = False
    molecule = Chem.MolFromSmiles(mapped_smiles, params)
    if molecule.GetNumAtoms() > 82:
        raise ValueError("E2 conformational check exceeds its bounded explicit-substrate size.")
    settings = AllChem.ETKDGv3(); settings.randomSeed = 42; settings.maxIterations = 300
    if AllChem.EmbedMolecule(molecule, settings) < 0:
        raise ValueError("The bounded substrate conformer could not be generated.")
    return check_conformations(molecule, hydrogen, beta, alpha, leaving)


def geometry(substrate, reagent, site):
    s = participants(substrate, reagent, site)
    try:
        return deepcopy(_geometry(Chem.MolToSmiles(substrate), *(s[k] for k in ("hydrogen", "beta", "alpha", "leaving"))))
    except (ValueError, RuntimeError) as exc:
        return {"status": "unresolved", "note": f"Conformational check unavailable: {exc} This is not proof of chemical impossibility; cyclic/unsupported structural cases are excluded independently."}
