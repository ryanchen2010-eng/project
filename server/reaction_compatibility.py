"""Explicit, per-pathway site compatibility and mapped edit contracts.

Distance is descriptive, never permission to call a group inert. A new pathway
must supply its own site/group checks; unknown groups fail closed. The initial
consumers supply their own policies, not a blanket expansion of other rules.
"""
from dataclasses import dataclass
from typing import Callable
from rdkit import Chem
if __package__:
    from .functional_groups import detect_groups
    from . import molecular_graph as graph, stereochemistry as stereo
else:
    from functional_groups import detect_groups
    import molecular_graph as graph, stereochemistry as stereo


@dataclass(frozen=True)
class SitePolicy:
    name: str
    elements: frozenset
    site_check: Callable
    group_check: Callable
    additional_check: Callable
    added_atoms: int = 0
    minimum_ring_size: int = 5
    maximum_product_atoms: int = 80
    extra_groups: tuple = ()


EXTRA_GROUPS = {"ether": Chem.MolFromSmarts("[C;!$(C=O)]-[OX2;H0;+0]-[C;!$(C=O)]"),
                "phenol": Chem.MolFromSmarts("[c]-[O;H1;+0]"),
                "peroxide": Chem.MolFromSmarts("[O]-[O]")}


def oxygen_closure_issue(molecule, oxygen, carbon, mechanism):
    """An existing O–C bond is not a possible new two-membered ring.

    For distinct nonbonded endpoints, the shortest existing path plus a new
    O–C edge counts the potential ring atoms. This flags competition, not a
    prediction that cyclization occurs. Policy eligibility stays unchanged.
    """
    path = Chem.GetShortestPath(molecule, oxygen, carbon)
    site = f"O atom {oxygen + 1} and C atom {carbon + 1}"
    if len(path) <= 2:
        return "unvalidated", f"{mechanism}: OH is already bonded to the electrophilic carbon ({site}); this directly heteroatom-substituted environment needs separate validation, not a new ring-closure bond."
    size = len(path)
    if size <= 6:
        kind = "epoxide" if size == 3 else "cyclic ether"
        return "competition", f"{mechanism}: a potential {size}-membered intramolecular {kind} closure connects {site} after OH deprotonation; competition with the selected pathway is unresolved."
    return None


def environment(molecule, site, additional_groups=()):
    """Return graph-indexed groups and their relationship to the actual site."""
    work = Chem.Mol(molecule)
    for atom in work.GetAtoms():
        atom.SetAtomMapNum(atom.GetIdx() + 1)
    features = [{"type": g["type"], "atomIndices": [m - 1 for m in g["atomMaps"]]}
                for g in detect_groups(work)]
    for name, query in [*EXTRA_GROUPS.items(), *additional_groups]:
        features.extend({"type": name, "atomIndices": list(match)} for match in work.GetSubstructMatches(query))
    for c, o in graph.find_carbonyls(work):
        if not any({c, o} <= set(g["atomIndices"]) for g in features):
            features.append({"type": "carbonyl", "atomIndices": [c, o]})
    for atom in work.GetAtoms():
        if atom.GetAtomicNum() == 8 and not any(atom.GetIdx() in g["atomIndices"] for g in features):
            features.append({"type": "unclassified oxygen", "atomIndices": [atom.GetIdx()]})
    unique, seen = [], set()
    for feature in features:
        key = feature["type"], tuple(sorted(feature["atomIndices"]))
        if key in seen:
            continue
        seen.add(key)
        distance = min(len(Chem.GetShortestPath(work, i, j)) - 1 if i != j else 0
                       for i in feature["atomIndices"] for j in site)
        feature.update(distance=distance, relation="reactive" if feature["type"] == "alkene" and set(feature["atomIndices"]) == set(site)
                       else "overlapping" if distance == 0 else "adjacent" if distance == 1 else "remote")
        unique.append(feature)
    return unique


def assess_site(molecule, site, policy):
    """Structural barriers vs unvalidated spectators vs competing chemistry."""
    site = tuple(site)
    result = {"version": 1, "policy": policy.name, "siteAtoms": list(site), "groups": [], "rejections": []}
    def reject(code, category, message, indices=()):
        result["rejections"].append({"code": code, "category": category, "message": message, "atomIndices": list(indices)})
    if len(site) != 2 or len(set(site)) != 2 or any(type(i) is not int or not 0 <= i < molecule.GetNumAtoms() for i in site):
        reject("invalid-site", "structural", "Choose two distinct atoms of the actual reactive bond.")
        result["eligible"] = False
        return result
    if len(Chem.GetMolFrags(molecule)) != 1:
        reject("disconnected-input", "structural", "This pathway needs one connected substrate; separate components are not spectators.")
        result["eligible"] = False
        return result
    for atom in molecule.GetAtoms():
        i = atom.GetIdx()
        if atom.GetSymbol() not in policy.elements:
            reject("unvalidated-element", "unvalidated", f"{atom.GetSymbol()} at substrate atom {i + 1} is outside the validated {policy.name} spectator set.", [i])
        if atom.GetFormalCharge() or atom.GetNumRadicalElectrons() or atom.GetIsotope() or atom.HasQuery():
            reject("unsupported-electronic-state", "structural", f"Substrate atom {i + 1} is charged, radical, isotopic or a query; this rule needs a neutral closed-shell specific structure.", [i])
    for ring in molecule.GetRingInfo().AtomRings():
        if len(ring) < policy.minimum_ring_size:
            reject("unvalidated-small-ring", "unvalidated", f"The {len(ring)}-membered ring at atoms {', '.join(str(i + 1) for i in ring)} needs strain/ring-opening compatibility validation.", ring)
    if Chem.AddHs(molecule).GetNumAtoms() + policy.added_atoms > policy.maximum_product_atoms:
        reject("product-size", "software-limit", f"The product would exceed {policy.maximum_product_atoms} explicit atoms including the added hydrogens.")
    stereo_issue = stereo.stereo_scope_issue(molecule, policy.name)
    if stereo_issue:
        reject("unsupported-stereo", "unvalidated", stereo_issue)
    site_issue = policy.site_check(molecule, site)
    if site_issue:
        reject("site-environment", "unvalidated", site_issue, site)
    result["groups"] = environment(molecule, site, policy.extra_groups)
    for group in result["groups"]:
        disposition, category, explanation = policy.group_check(molecule, site, group)
        group.update(disposition=disposition, explanation=explanation)
        if disposition == "reactive":
            group["relation"] = "reactive"
        if disposition == "rejected":
            reject("group-compatibility", category, explanation, group["atomIndices"])
    for code, category, message, indices in policy.additional_check(molecule, site):
        reject(code, category, message, indices)
    result["eligible"] = not result["rejections"]
    return result


def mapped_report(report, substrate, edits, *, charge_changes=(), consumed_tetrahedral_centers=(), inverted_substitutions=(), eliminations=(), solvolyses=(), e1_eliminations=(), consumed_double_bonds=()):
    """Translate graph indices into the exact reaction map namespace."""
    mapped = lambda indices: [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in indices]
    return {"version": report["version"], "policy": report["policy"], "eligible": report["eligible"],
            "reactiveAtomMaps": sorted({m for e in edits for m in e["atomMaps"]}),
            "substrateSiteMaps": mapped(report["siteAtoms"]),
            "groups": [{**{k: v for k, v in g.items() if k != "atomIndices"}, "atomMaps": mapped(g["atomIndices"])} for g in report["groups"]],
            "editContract": edits,
            **({"chargeChanges": list(charge_changes)} if charge_changes else {}),
            **({"consumedTetrahedralCenters": list(consumed_tetrahedral_centers)} if consumed_tetrahedral_centers else {}),
            **({"consumedDoubleBonds": list(consumed_double_bonds)} if consumed_double_bonds else {}),
            **({"invertedSubstitutions": list(inverted_substitutions)} if inverted_substitutions else {}),
            **({"eliminations": list(eliminations)} if eliminations else {}),
            **({"solvolyses": list(solvolyses)} if solvolyses else {}),
            **({"e1Eliminations": list(e1_eliminations)} if e1_eliminations else {}),
            "validation": {"atomIdentity": "verified", "charge": "verified", "unaffectedBonds": "verified",
                           "unaffectedStereo": "verified", "mappedSerialization": "verified"}}


def _mapped_atoms(molecule):
    atoms = {a.GetAtomMapNum(): a for a in molecule.GetAtoms()}
    if len(atoms) != molecule.GetNumAtoms() or any(m <= 0 for m in atoms):
        raise ValueError("Site compatibility requires unique positive atom maps.")
    return atoms


def mapped_bonds(molecule):
    return {frozenset((b.GetBeginAtom().GetAtomMapNum(), b.GetEndAtom().GetAtomMapNum())): b.GetBondTypeAsDouble()
            for b in molecule.GetBonds()}


def validate_edit_contract(before, after, edits, *, consumed_double_bonds=(), consumed_tetrahedral_centers=(),
                           inverted_substitutions=(), eliminations=(), solvolyses=(), e1_eliminations=(), charge_changes=(), expected_fragments=None):
    """Only authorized bond edits are allowed; spectator identity is exact.

Charge is unchanged by default. A redox consumer must declare exact, balanced
per-atom charge changes; there is no flag disabling charge conservation. Stereo
loss is allowed only at a checked consumed C=C or a mapped reactive alcohol
center that becomes a planar carbonyl, or at the exact alpha/beta centers of
a declared hydroxide E2 edit, or at the checked reacting carbon of an exact
water SN1 stage or the exact participating atoms of a checked E1 elementary
stage, never at an arbitrary distant center.
"""
    original, product = _mapped_atoms(before), _mapped_atoms(after)
    identity = lambda atoms: {m: (a.GetAtomicNum(), a.GetIsotope(), a.GetFormalCharge(), a.GetNumRadicalElectrons()) for m, a in atoms.items()}
    expected_identity = identity(original)
    charge_maps = set()
    for change in charge_changes:
        number = change["atomMap"]
        if (type(number) is not int or number not in original or number in charge_maps
                or type(change["before"]) is not int or type(change["after"]) is not int
                or original[number].GetFormalCharge() != change["before"] or change["before"] == change["after"]):
            raise ValueError("The per-atom charge edit contract is invalid or duplicated.")
        charge_maps.add(number)
        element, isotope, _, radical = expected_identity[number]
        expected_identity[number] = (element, isotope, change["after"], radical)
    if sum(c["after"] - c["before"] for c in charge_changes) != 0:
        raise ValueError("Declared charge edits must conserve total charge.")
    if expected_identity != identity(product):
        raise ValueError("The site edit changed an atom's identity, charge or electronic state.")
    expected = mapped_bonds(before)
    changed = set()
    for edit in edits:
        pair = frozenset(edit["atomMaps"])
        if len(pair) != 2 or pair in changed or not pair <= original.keys() or edit["before"] == edit["after"]:
            raise ValueError("The reactive-bond edit contract is invalid or duplicated.")
        changed.add(pair)
        if expected.get(pair) != edit["before"]:
            raise ValueError("The reactive bond does not match its declared initial state.")
        if edit["after"] is None:
            expected.pop(pair)
        else:
            expected[pair] = edit["after"]
    if mapped_bonds(after) != expected:
        raise ValueError("An unaffected bond changed or a required reactive bond edit was missed.")
    for pair in consumed_double_bonds:
        pair = frozenset(pair)
        if mapped_bonds(before).get(pair) != 2 or expected.get(pair) != 1 or pair not in changed:
            raise ValueError("Only an explicitly reduced C=C may lose its alkene geometry.")
        ends = [product[m].GetIdx() for m in pair]
        if after.GetBondBetweenAtoms(*ends).GetStereo() != Chem.BondStereo.STEREONONE:
            raise ValueError("Consumed alkene geometry was incorrectly retained on a single bond.")
    if expected_fragments is not None and len(Chem.GetMolFrags(after)) != expected_fragments:
        raise ValueError("The product has an unexpected number of connected components.")
    for number in consumed_tetrahedral_centers:
        atom = original.get(number)
        if atom is None or not any(number in e["atomMaps"] and e["before"] == 1 and e["after"] == 2
                                  and all(original[m].GetAtomicNum() in {6, 8} for m in e["atomMaps"]) for e in edits):
            raise ValueError("A consumed tetrahedral center must belong to a declared alcohol-to-carbonyl bond edit.")
    for substitution in inverted_substitutions:
        center, leaving, incoming = (substitution[k] for k in ("center", "leaving", "incoming"))
        required = {(frozenset((center, leaving)), 1, None), (frozenset((center, incoming)), None, 1)}
        actual = {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in edits}
        if not required <= actual:
            raise ValueError("An SN2 inversion must accompany the exact declared bond cleavage and formation.")
    for elimination in eliminations:
        alpha, beta, hydrogen, leaving, base = (elimination[k] for k in ("alpha", "beta", "hydrogen", "leaving", "base"))
        required = {(frozenset((alpha, leaving)), 1, None), (frozenset((beta, hydrogen)), 1, None),
                    (frozenset((alpha, beta)), 1, 2), (frozenset((base, hydrogen)), None, 1)}
        actual = {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in edits}
        if (not required <= actual or len(set((alpha, beta, hydrogen, leaving, base))) != 5
                or base not in original or original[base].GetAtomicNum() != 8
                or original[base].GetFormalCharge() != -1 or product[base].GetFormalCharge()
                or original[leaving].GetFormalCharge() or product[leaving].GetFormalCharge() != -1):
            raise ValueError("An E2 stereo permission requires its exact hydroxide C–H/C–X cleavage, C=C formation and proton transfer.")
    for substitution in solvolyses:
        # No blanket permission to erase a tetrahedron: the stage must have
        # exactly the ionization/water capture/proton transfer being claimed.
        center, leaving, incoming, hydrogen = (substitution[k] for k in ("center", "leaving", "incoming", "hydrogen"))
        stage = substitution["stage"]
        if any(type(m) is not int or m <= 0 or m not in original or m not in product for m in (center, leaving, incoming, hydrogen)):
            raise ValueError("SN1 requires actual mapped reaction atoms.")
        required = {
            "net": {(frozenset((center, leaving)), 1, None), (frozenset((center, incoming)), None, 1),
                    (frozenset((incoming, hydrogen)), 1, None), (frozenset((leaving, hydrogen)), None, 1)},
            "ionization": {(frozenset((center, leaving)), 1, None)},
            "capture": {(frozenset((center, incoming)), None, 1)},
        }
        required_charges = {"net": set(), "ionization": {(center, 0, 1), (leaving, 0, -1)},
                            "capture": {(center, 1, 0), (incoming, 0, 1)}}
        if stage == "deprotonation":
            base = substitution.get("solventBase")
            if type(base) is not int or base not in original or base in {center, leaving, incoming, hydrogen} or original[base].GetAtomicNum() != 8:
                raise ValueError("SN1 deprotonation needs a distinct actual solvent-water oxygen.")
            required[stage] = {(frozenset((incoming, hydrogen)), 1, None), (frozenset((base, hydrogen)), None, 1)}
            required_charges[stage] = {(incoming, 1, 0), (base, 0, 1)}
            if (original[base].GetFormalCharge() or original[base].GetDegree() != 2
                    or any(n.GetAtomicNum() != 1 for n in original[base].GetNeighbors())):
                raise ValueError("SN1 proton transfer uses one actual neutral solvent water, not an assumed base.")
        actual = {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in edits}
        charges = {(c["atomMap"], c["before"], c["after"]) for c in charge_changes}
        if stage not in required or actual != required[stage] or charges != required_charges[stage]:
            raise ValueError("An SN1 configuration-loss permission needs the exact declared elementary-stage edits and charges.")
        water = original[incoming]
        expected_degree = 3 if stage == "deprotonation" else 2
        expected_charge = 1 if stage == "deprotonation" else 0
        if (water.GetAtomicNum() != 8 or water.GetDegree() != expected_degree or water.GetFormalCharge() != expected_charge
                or sum(n.GetAtomicNum() == 1 for n in water.GetNeighbors()) != 2
                or hydrogen not in {n.GetAtomMapNum() for n in water.GetNeighbors()}):
            raise ValueError("This SN1 stage must use the actual water/oxonium oxygen and its two original hydrogens.")
    for elimination in e1_eliminations:
        alpha, beta, hydrogen, leaving = (elimination[k] for k in ("alpha", "beta", "hydrogen", "leaving"))
        if len({alpha, beta, hydrogen, leaving}) != 4 or any(type(m) is not int or m <= 0 or m not in original or m not in product for m in (alpha, beta, hydrogen, leaving)):
            raise ValueError("E1 requires distinct actual mapped alpha, beta, H and halogen atoms.")
        stage = elimination["stage"]
        required = {"net": {(frozenset((alpha, leaving)), 1, None), (frozenset((beta, hydrogen)), 1, None), (frozenset((alpha, beta)), 1, 2), (frozenset((leaving, hydrogen)), None, 1)},
                    "ionization": {(frozenset((alpha, leaving)), 1, None)}}
        required_charges = {"net": set(), "ionization": {(alpha, 0, 1), (leaving, 0, -1)}}
        if stage in {"ionization", "elimination"}:
            base = elimination.get("base")
            if type(base) is not int or base <= 0 or base not in original or base in {alpha, beta, hydrogen, leaving}:
                raise ValueError("E1 needs one distinct actual solvent-water oxygen.")
            water = original[base]
            if (water.GetAtomicNum() != 8 or water.GetFormalCharge() or water.GetDegree() != 2
                    or any(n.GetAtomicNum() != 1 for n in water.GetNeighbors())
                    or any(b.GetBondType() != Chem.BondType.SINGLE for b in water.GetBonds())):
                raise ValueError("E1 uses neutral solvent water, not hydroxide or an assumed base.")
            required["elimination"] = {(frozenset((beta, hydrogen)), 1, None), (frozenset((alpha, beta)), 1, 2), (frozenset((base, hydrogen)), None, 1)}
            required_charges["elimination"] = {(alpha, 1, 0), (base, 0, 1)}
        actual = {(frozenset(e["atomMaps"]), e["before"], e["after"]) for e in edits}
        charges = {(c["atomMap"], c["before"], c["after"]) for c in charge_changes}
        if stage not in required or actual != required[stage] or charges != required_charges[stage]:
            raise ValueError("E1 stereo permission requires the exact ionization or subsequent beta-H step, not arbitrary or concerted edits.")
    stereo.validate_retained_stereo(before, after, consumed_double_bonds=consumed_double_bonds,
                                   consumed_tetrahedral_centers=consumed_tetrahedral_centers,
                                   inverted_substitutions=inverted_substitutions, eliminations=eliminations, solvolyses=solvolyses, e1_eliminations=e1_eliminations, context="The site edit")
    # Validate the exact serialized structures used by public preview/run.
    params = Chem.SmilesParserParams()
    params.removeHs = False
    restored = Chem.MolFromSmiles(Chem.MolToSmiles(after), params)
    if restored is None or identity(_mapped_atoms(restored)) != expected_identity or mapped_bonds(restored) != expected:
        raise ValueError("The mapped product did not preserve its edit contract through serialization.")
    stereo.validate_retained_stereo(before, restored, consumed_double_bonds=consumed_double_bonds,
                                   consumed_tetrahedral_centers=consumed_tetrahedral_centers,
                                   inverted_substitutions=inverted_substitutions, eliminations=eliminations, solvolyses=solvolyses, e1_eliminations=e1_eliminations, context="The serialized site edit")
