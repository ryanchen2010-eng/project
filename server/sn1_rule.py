"""Water-only, screened carbocation solvolysis with exact elementary contracts.

Tertiary/benzylic, screened Me/Me or Me/Et secondary and symmetric-allyl model, not arbitrary
solvolysis, rearrangement prediction, perfect racemization or an experimental
selectivity claim. Other pathways do not inherit these permissions.
"""
from rdkit import Chem
if __package__:
    from . import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, carbocation_compatibility as carbocation
else:
    import molecular_graph as graph, reaction_compatibility as compatibility, stereochemistry as stereo, carbocation_compatibility as carbocation

SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction"
CHARACTERISTICS_SOURCE = "https://openstax.org/books/organic-chemistry/pages/11-5-characteristics-of-the-sn1-reaction"
ETHER_SOURCE = "https://openstax.org/books/organic-chemistry/pages/18-3-reactions-of-ethers-acidic-cleavage"
SHIFT_SOURCE = "https://openstax.org/books/organic-chemistry/pages/7-11-evidence-for-the-mechanism-of-electrophilic-additions-carbocation-rearrangements"
ETHER_QUERY = Chem.MolFromSmarts("[#6;!$(C=O)]-[OX2;H0;+0]-[#6;!$(C=O)]")
NONALKYL_HALIDE = Chem.MolFromSmarts("[#6;!X4]-[F,Cl,Br,I]")


def sites(molecule):
    return graph.find_alkyl_halides(molecule)


def distance(molecule, a, b):
    return len(Chem.GetShortestPath(molecule, a, b)) - 1 if a != b else 0


def symmetric_allyl(molecule, site):
    """A CH2–X/CH2 allyl pair: the two resonance termini give one constitution.

The central sp² carbon may carry H or an ordinary saturated carbon substituent.
No substituted unequal termini, alkene geometry or regioselectivity is inferred.
"""
    carbon = molecule.GetAtomWithIdx(site[0])
    neighbors = graph.carbon_neighbors(carbon)
    if len(neighbors) != 1 or graph.attached_hydrogens(carbon) != 2:
        return None
    middle = neighbors[0]
    if middle.GetIsAromatic() or middle.GetHybridization() != Chem.HybridizationType.SP2:
        return None
    doubles = [b for b in middle.GetBonds() if b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(middle).GetAtomicNum() == 6]
    if len(doubles) != 1:
        return None
    end = doubles[0].GetOtherAtom(middle)
    if (end.GetIsAromatic() or graph.attached_hydrogens(end) != 2 or len(graph.carbon_neighbors(end)) != 1
            or doubles[0].GetStereo() != Chem.BondStereo.STEREONONE or carbon.IsInRing() or middle.IsInRing() or end.IsInRing()
            or any(n.GetAtomicNum() not in {1, 6} for n in middle.GetNeighbors())):
        return None
    for n in graph.carbon_neighbors(middle):
        if n.GetIdx() not in {carbon.GetIdx(), end.GetIdx()} and (n.GetHybridization() != Chem.HybridizationType.SP3 or n.GetIsAromatic()):
            return None
    return (middle.GetIdx(), end.GetIdx())


def classification(molecule, site):
    carbon = molecule.GetAtomWithIdx(site[0])
    if any(n.GetIsAromatic() for n in graph.carbon_neighbors(carbon)):
        return "benzylic resonance"
    if symmetric_allyl(molecule, site):
        return "symmetric allylic resonance"
    return carbocation.alkyl_basis(molecule, site) or "unsupported ordinary alkyl cation"

def halide_environment(molecule, site):
    return carbocation.halide_issue(molecule, site, "SN1")

def rearrangement_issue(molecule, site):
    allyl = symmetric_allyl(molecule, site)
    return carbocation.rearrangement_issue(molecule, site, "SN1", resonance_neighbors=(allyl[0],) if allyl else ())

def site_check(molecule, site):
    issue = halide_environment(molecule, site)
    if issue:
        return issue
    if classification(molecule, site) == "unsupported ordinary alkyl cation":
        if graph.is_allylic_or_benzylic(molecule.GetAtomWithIdx(site[0])):
            return "Unequal/substituted allylic termini need resonance-site/regioselectivity validation; only the terminal-equivalent CH2/CH2 allyl case is enabled."
        return "Ordinary primary/methyl and secondary aliphatic ionization beyond the screened Me/Me or Me/Et arm scope are not validated by this water-based SN1 model; unsupported does not mean solvolysis is chemically impossible."
    if (symmetric_allyl(molecule, site) is None and any(n.GetHybridization() == Chem.HybridizationType.SP2 and not n.GetIsAromatic()
                                                   for n in graph.carbon_neighbors(molecule.GetAtomWithIdx(site[0])))):
        return "Additional allylic/conjugated carbocation environments can support a bounded E1 option but water capture at inequivalent resonance termini needs separate SN1 product/regioselectivity validation; ionization eligibility alone does not validate capture."
    return rearrangement_issue(molecule, site)


def group_check(molecule, site, group):
    kind, indices = group["type"], group["atomIndices"]
    if kind == "haloalkane":
        other = next((s for s in sites(molecule) if set(s) == set(indices)), None)
        issue = halide_environment(molecule, other) if other else "This halide has no validated ordinary carbon environment."
        if issue:
            return "rejected", "unvalidated", issue
        if set(other) == set(site):
            return "reactive", "validated", f"Selected {classification(molecule, site)}: C–X ionizes, water attacks and a separate proton transfer gives an unassigned alcohol."
        if distance(molecule, site[0], other[0]) < 3:
            return "rejected", "competition", "Nearby multiple halides can produce coupled ionization/elimination; independent SN1 sites need separate validation."
        issue = site_check(molecule, other)
        if issue is None:
            return "alternative-site", "bounded", "Another screened carbocation-forming C–X remains unchanged in this one-site net option. Further solvolysis, E1 and capture by newly formed OH are not excluded; selective mono-substitution is not predicted."
        carbon = molecule.GetAtomWithIdx(other[0])
        if graph.substitution_degree(carbon) <= 1 and not graph.is_allylic_or_benzylic(carbon):
            return "preserved", "bounded", "This separated ordinary primary/methyl C–X does not receive SN1 ionization permission and remains in the net structure. Slow substitution or later chemistry is not claimed absent."
        return "rejected", "unvalidated", "An additional halide has unvalidated competing carbocation chemistry: " + issue
    if kind in {"alcohol", "ether"}:
        oxygen = next((molecule.GetAtomWithIdx(i) for i in indices if molecule.GetAtomWithIdx(i).GetAtomicNum() == 8), None)
        if oxygen is None:
            return "rejected", "unvalidated", "This oxygen group has no ordinary SN1 spectator environment."
        # Include every supported ionizable site, not only the chosen one.
        for other in sites(molecule):
            if classification(molecule, other) != "unsupported ordinary alkyl cation":
                ring_size = distance(molecule, oxygen.GetIdx(), other[0]) + 1
                if ring_size <= 3:
                    return "rejected", "unvalidated", "Direct/vicinal oxygen needs separate oxocarbenium or neighboring-group validation; it is not a screened distant spectator."
                if ring_size <= 6:
                    return "rejected", "competition", f"This oxygen lies on a potential {ring_size}-membered intramolecular carbocation-capture path; neighboring-group participation/cyclization versus water attack is unvalidated."
        if kind == "alcohol":
            other = next((s for s in graph.find_alcohols(molecule) if set(s) == set(indices)), None)
            if other is None:
                return "rejected", "unvalidated", "Only neutral saturated primary/secondary remote alcohols are screened here."
            carbon = molecule.GetAtomWithIdx(other[0])
            if (graph.substitution_degree(carbon) >= 3 or graph.is_allylic_or_benzylic(carbon)
                    or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1):
                return "rejected", "competition", "Tertiary/benzylic/allylic or geminal-O alcohols can introduce acid-sensitive ionization/cleavage; remote distance alone does not validate their retention."
            return "preserved", "bounded", "This screened distant saturated primary/secondary OH keeps its bonds in the net solvolysis. Larger-ring/intermolecular capture, proton equilibria and acid accumulation are not predicted."
        if oxygen.GetDegree() != 2 or all(c.GetIsAromatic() for c in oxygen.GetNeighbors()):
            return "rejected", "unvalidated", "Only ordinary remote dialkyl/aryl–alkyl ethers are screened; diaryl or nonordinary oxygen environments need separate validation."
        for carbon in oxygen.GetNeighbors():
            if (carbon.GetAtomicNum() != 6 or sum(n.GetAtomicNum() == 8 for n in carbon.GetNeighbors()) != 1
                    or (not carbon.GetIsAromatic() and (carbon.GetHybridization() != Chem.HybridizationType.SP3
                         or graph.substitution_degree(carbon) >= 3 or graph.is_allylic_or_benzylic(carbon)))):
                return "rejected", "competition", "Tertiary/benzyl/allyl, enol or acetal/ketal ethers can undergo acid-driven cleavage or coupled capture; they are not validated SN1 spectators."
        return "preserved", "bounded", "The screened distant ordinary ether keeps its C–O bonds in this net option. Strong-acid cleavage, larger-ring capture and solution-specific stability are not predicted; the medium selector is not a pH model."
    if kind == "aromatic ring":
        if any(molecule.GetAtomWithIdx(i).GetAtomicNum() != 6 for i in indices):
            return "rejected", "unvalidated", "Heteroaromatic protonation/resonance and capture are outside this water SN1 policy."
        return "preserved", "bounded", "The carbocyclic aromatic skeleton remains intact; benzylic positive charge is delocalized and the drawn cation is one resonance contributor, not localized charge-density prediction."
    if kind == "alkene":
        allyl = symmetric_allyl(molecule, site)
        if allyl and set(indices) == set(allyl):
            return "preserved", "validated", "This specific allyl pi bond supports the symmetric CH2/CH2 cation. A localized contributor is shown; equivalent termini give the same constitution, not a quantified atom-path or SN1/SN2/E1 ratio."
        return "rejected", "competition", "Additional/unequal unsaturation can introduce resonance regioisomers or cationic cyclization; that SN1 selectivity is not modeled."
    return "rejected", "unvalidated", f"The additional {kind} has no validated water/carbocation compatibility policy; it is not assumed inert."


POLICY = compatibility.SitePolicy("water SN1 solvolysis", frozenset({"C", "H", "O", "Cl", "Br", "I"}),
                                  site_check, group_check, lambda molecule, site: (), added_atoms=1,
                                  extra_groups=(("ether", ETHER_QUERY), ("non-alkyl halide", NONALKYL_HALIDE)))


def assess(molecule, site):
    return compatibility.assess_site(molecule, site, POLICY)


def water_oxygen(molecule):
    atoms = list(molecule.GetAtoms())
    oxygens = [a for a in atoms if a.GetAtomicNum() == 8]
    if (len(atoms) != 3 or len(oxygens) != 1 or molecule.GetNumBonds() != 2
            or oxygens[0].GetDegree() != 2 or graph.attached_hydrogens(oxygens[0]) != 2
            or any(a.GetAtomicNum() not in {1, 8} or a.GetFormalCharge() or a.GetIsotope() or a.GetNumRadicalElectrons() or a.HasQuery() for a in atoms)
            or any(b.GetBondType() != Chem.BondType.SINGLE for b in molecule.GetBonds())):
        raise ValueError("SN1 uses one actual neutral water nucleophile; hydroxide, alcohols and other nucleophiles are not substituted by name or formula.")
    return oxygens[0]


def participants(substrate, reagent, site, stage="net", solvent=None):
    oxygen = water_oxygen(reagent)
    s = {"center": substrate.GetAtomWithIdx(site[0]).GetAtomMapNum(),
         "leaving": substrate.GetAtomWithIdx(site[1]).GetAtomMapNum(), "incoming": oxygen.GetAtomMapNum(),
         "hydrogen": min(n.GetAtomMapNum() for n in oxygen.GetNeighbors()), "stage": stage}
    if solvent is not None:
        s["solventBase"] = water_oxygen(solvent).GetAtomMapNum()
    return s


def stage_edits(s):
    c, x, o, h = (s[k] for k in ("center", "leaving", "incoming", "hydrogen"))
    definitions = {
        "net": [(c, x, 1, None), (c, o, None, 1), (o, h, 1, None), (x, h, None, 1)],
        "ionization": [(c, x, 1, None)], "capture": [(c, o, None, 1)],
        "deprotonation": [(o, h, 1, None), (s.get("solventBase"), h, None, 1)]}
    if s["stage"] not in definitions:
        raise ValueError("Unknown SN1 stage.")
    return [{"atomMaps": [a, b], "before": before, "after": after} for a, b, before, after in definitions[s["stage"]]]


def stage_charges(s):
    c, x, o = (s[k] for k in ("center", "leaving", "incoming"))
    changes = {"net": [], "ionization": [(c, 0, 1), (x, 0, -1)],
               "capture": [(c, 1, 0), (o, 0, 1)], "deprotonation": [(o, 1, 0), (s.get("solventBase"), 0, 1)]}
    if s["stage"] not in changes:
        raise ValueError("Unknown SN1 stage.")
    return [{"atomMap": m, "before": before, "after": after} for m, before, after in changes[s["stage"]]]


def edit_contract(substrate, reagent, site):
    return stage_edits(participants(substrate, reagent, site))


def unassign_reacting_center(editor, number):
    next(a for a in editor.GetAtoms() if a.GetAtomMapNum() == number).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)


def validate(before, after, substrate, reagent, site, stage="net", solvent=None):
    report = assess(substrate, site)
    if not report["eligible"]:
        raise ValueError(" ".join(r["message"] for r in report["rejections"]))
    s = participants(substrate, reagent, site, stage, solvent)
    fragments = {"net": 2, "ionization": 4, "capture": 3, "deprotonation": 3}[stage]
    compatibility.validate_edit_contract(before, after, stage_edits(s), charge_changes=stage_charges(s),
                                        solvolyses=[s], expected_fragments=fragments)
