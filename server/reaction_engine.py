"""Bounded structural reaction engine. No names/formulas/CIDs decide eligibility.

Detection -> scope/requirements -> site candidates -> explicit mapped edits ->
sanitization/conservation -> product fragments. These are possible net pathways,
not predictions of rates, selectivity, stereoisomers or experimental conversion.
"""
from collections import Counter
from rdkit import Chem

if __package__:
    from .product_naming import simple_product_name
else:
    from product_naming import simple_product_name

if __package__:
    from . import molecular_graph as graph
    from . import epoxidation_rule, dihydroxylation_rule, alkyne_partial_hydrogenation_rule, alkyne_complete_hydrogenation_rule, alkyne_halogenation_rule, alkyne_hydrohalogenation_rule
    from . import extended_reaction_rules, aldehyde_oxidation_conditions
    from . import ester_rules, alcohol_dehydration_rule, alcohol_substitution_rule, primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule
    from . import hydrogenation_rule, carbonyl_hydrogenation_rule, alcohol_oxidation_rule, sn2_rule, e2_rule, sn1_rule, e1_rule, hydration_rule, hydrohalogenation_rule, bromination_rule, chlorination_rule, reaction_compatibility
    from .stereochemistry import invert_sn2, inspect_stereochemistry
    from .reaction_diagrams import _species, _combine, _remove, _add, _order, _charge, _finish, _identity, _hydrogens
else:
    import molecular_graph as graph
    import epoxidation_rule, dihydroxylation_rule, alkyne_partial_hydrogenation_rule, alkyne_complete_hydrogenation_rule, alkyne_halogenation_rule, alkyne_hydrohalogenation_rule
    import extended_reaction_rules, aldehyde_oxidation_conditions
    import ester_rules, alcohol_dehydration_rule, alcohol_substitution_rule, primary_alcohol_oxidation_rule, secondary_alcohol_oxidation_rule
    import hydrogenation_rule, carbonyl_hydrogenation_rule, alcohol_oxidation_rule, sn2_rule, e2_rule, sn1_rule, e1_rule, hydration_rule, hydrohalogenation_rule, bromination_rule, chlorination_rule, reaction_compatibility
    from stereochemistry import invert_sn2, inspect_stereochemistry
    from reaction_diagrams import _species, _combine, _remove, _add, _order, _charge, _finish, _identity, _hydrogens


SOURCES = {
    "alkene": "https://openstax.org/books/organic-chemistry/pages/8-summary",
    "orientation": "https://openstax.org/books/organic-chemistry/pages/7-8-orientation-of-electrophilic-additions-markovnikovs-rule",
    "alcohol": "https://openstax.org/books/organic-chemistry/pages/17-7-oxidation-of-alcohols",
    "aldehyde": "https://openstax.org/books/organic-chemistry/pages/19-3-oxidation-of-aldehydes-and-ketones",
    "carbonyl": "https://openstax.org/books/organic-chemistry/pages/17-4-alcohols-from-carbonyl-compounds-reduction",
    "ester": "https://openstax.org/books/organic-chemistry/pages/21-6-chemistry-of-esters",
    "substitution": "https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction",
    "sn1": "https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction",
    "elimination": "https://openstax.org/books/organic-chemistry/pages/11-8-the-e2-reaction-and-the-deuterium-isotope-effect",
    "e1": "https://openstax.org/books/organic-chemistry/pages/11-10-the-e1-and-e1cb-reactions",
}
PREFIX = {"Hydrogenation": "hydrogenation", "Bromination": "bromination", "Chlorination": "chlorination",
          "Hydrohalogenation": "hydrohalogenation", "Hydration": "hydration", "Alcohol oxidation": "oxidation",
          "Carbonyl hydrogenation": "reduction", "Esterification": "esterification", "Ester hydrolysis": "ester-hydrolysis",
          "Aldehyde oxidation": "aldehyde-oxidation", "Epoxidation": "epoxidation"}
PREFIX.update({name: name.lower().replace(" ", "-") for name in (
    "Alcohol dehydration", "Alcohol substitution", "Ester saponification", "Alkyne hydrogenation",
    "Alkyne partial hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation", "Alkene dihydroxylation", "Polymerization model")})


def reagent_role(molecule):
    """Identify small reagent graphs, including the spectator of hypochlorite."""
    atoms = list(molecule.GetAtoms())
    if len(atoms) == 2 and molecule.GetNumBonds() == 1:
        a, b = atoms
        if a.GetAtomicNum() == b.GetAtomicNum() == 1 and not any(x.GetFormalCharge() for x in atoms):
            return "hydrogen"
        if a.GetSymbol() == b.GetSymbol() and a.GetSymbol() in {"Cl", "Br"} and not any(x.GetFormalCharge() for x in atoms):
            return "halogen"
    if len(atoms) == 1 and atoms[0].GetAtomicNum() == 8:
        if atoms[0].GetFormalCharge() == -1 and graph.attached_hydrogens(atoms[0]) == 1:
            return "hydroxide"
        if not atoms[0].GetFormalCharge() and graph.attached_hydrogens(atoms[0]) == 2:
            return "water"
    if len(atoms) == 1 and atoms[0].GetSymbol() in {"Cl", "Br", "I"} and graph.attached_hydrogens(atoms[0]) == 1:
        return "hydrogen-halide"
    fragments = Chem.GetMolFrags(molecule, asMols=True)
    if len(fragments) == 2:
        anions = [f for f in fragments if f.GetNumAtoms() == 2 and f.GetNumBonds() == 1
                  and sorted((a.GetSymbol(), a.GetFormalCharge()) for a in f.GetAtoms()) == [("Cl", 0), ("O", -1)]]
        cations = [f for f in fragments if f.GetNumAtoms() == 1 and f.GetAtomWithIdx(0).GetSymbol() in {"Li", "Na", "K", "Rb", "Cs"}
                   and f.GetAtomWithIdx(0).GetFormalCharge() == 1]
        if anions and cations:
            return "hypochlorite"
    if epoxidation_rule.peroxyacid_sites(molecule):
        return "peroxyacid"
    return extended_reaction_rules.reagent_role(molecule)


def scope_issue(molecule, elements, allow_stereo=False):
    if any(a.GetSymbol() not in elements or a.GetFormalCharge() or a.GetNumRadicalElectrons()
           or a.GetIsotope() or a.HasQuery() for a in molecule.GetAtoms()):
        return "This rule needs a neutral, closed-shell substrate in its supported element family."
    if not allow_stereo and any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in molecule.GetAtoms()):
        return "Specified stereocenters are not supported by these connectivity-only transformations."
    if any(len(ring) < 5 for ring in molecule.GetRingInfo().AtomRings()):
        return "Strained rings need additional reaction rules."
    return None


def validate_products(before, after, main_map, allow_carboxylate=False):
    """Sanitize and enforce identity, elements, explicit H and net charge."""
    Chem.SanitizeMol(after)
    before_atoms = {a.GetAtomMapNum(): (a.GetAtomicNum(), a.GetIsotope()) for a in before.GetAtoms()}
    after_atoms = {a.GetAtomMapNum(): (a.GetAtomicNum(), a.GetIsotope()) for a in after.GetAtoms()}
    if len(before_atoms) != before.GetNumAtoms() or len(after_atoms) != after.GetNumAtoms() or before_atoms != after_atoms:
        raise ValueError("Atom conservation failed.")
    if sum(a.GetFormalCharge() for a in before.GetAtoms()) != sum(a.GetFormalCharge() for a in after.GetAtoms()):
        raise ValueError("Charge conservation failed.")
    if any(a.GetNumRadicalElectrons() or a.GetNumImplicitHs() for a in after.GetAtoms()):
        raise ValueError("Unexpected radical or implicit hydrogen in an explicit mapped transformation.")
    bonds = [tuple(sorted((b.GetBeginAtomIdx(), b.GetEndAtomIdx()))) for b in after.GetBonds()]
    if len(bonds) != len(set(bonds)):
        raise ValueError("Duplicate product bond.")
    fragments = list(Chem.GetMolFrags(after, asMols=True))
    main = next((f for f in fragments if any(a.GetAtomMapNum() == main_map for a in f.GetAtoms())), None)
    charge_supported = (allow_carboxylate and sum(a.GetFormalCharge() for a in main.GetAtoms()) == -1
                        and all(not a.GetFormalCharge() or (a.GetSymbol() == "O" and a.GetFormalCharge() == -1) for a in main.GetAtoms())) if main is not None else False
    if main is None or main.GetNumAtoms() > 80 or (any(a.GetFormalCharge() for a in main.GetAtoms()) and not charge_supported):
        raise ValueError("This product is outside the neutral, at-most-80-explicit-atom model scope.")
    return [main, *[f for f in fragments if f is not main]]


def transform(mechanism, inputs, site, *, dihydroxylation_profile=None):
    """One source of truth for product chemistry AND 2D/3D atom mapping.

Site indices address the first input's heavy-atom graph. No first-match search
occurs here; the chosen candidate is applied explicitly.
"""
    combined = _combine(inputs)
    editor = Chem.RWMol(combined)
    substrate = inputs[0]["mol"]
    maps = [substrate.GetAtomWithIdx(i).GetAtomMapNum() for i in
            (site[:2] if mechanism in extended_reaction_rules.MECHANISMS else site[:3] if mechanism == "Esterification" else site)]
    reagent = inputs[1]["mol"] if len(inputs) > 1 else None
    if mechanism in ester_rules.PATHWAYS:
        issue = ester_rules.site_issue(substrate, site)
        if issue:
            raise ValueError(issue)
    def atom_of(symbol):
        return next(a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetSymbol() == symbol)
    if extended_reaction_rules.edit(mechanism, editor, combined, inputs, site):
        pass
    elif mechanism == "Epoxidation":
        epoxidation_rule.edit(editor, combined, substrate, reagent, site)
    elif mechanism == "Alkene dihydroxylation":
        dihydroxylation_rule.edit(editor, combined, substrate, reagent, site)
    elif mechanism in {"SN1", "SN2", "E1", "E2"}:
        carbon, leaving = maps[:2]
        _remove(editor, carbon, leaving)
        if mechanism in {"SN1", "SN2"}:
            oxygen = atom_of("O")
            _add(editor, carbon, oxygen)
            if mechanism == "SN2":
                _charge(editor, oxygen, 0); _charge(editor, leaving, -1)
                invert_sn2(combined, editor, carbon, leaving, oxygen)
            else:
                h = _hydrogens(combined, oxygen)[0]
                _remove(editor, oxygen, h); _add(editor, leaving, h)
                sn1_rule.unassign_reacting_center(editor, carbon)
        else:
            beta = maps[2]
            h = e1_rule.participants(substrate, site)["hydrogen"] if mechanism == "E1" else _hydrogens(combined, beta)[0]
            _remove(editor, beta, h); _order(editor, carbon, beta, 2)
            if mechanism == "E2":
                oxygen = atom_of("O")
                _add(editor, oxygen, h); _charge(editor, oxygen, 0); _charge(editor, leaving, -1)
                e2_rule.apply_stereo(combined, editor, e2_rule.participants(substrate, reagent, site))
            else:
                _add(editor, leaving, h)
                e1_rule.apply_stereo(editor, e1_rule.participants(substrate, site))
    elif mechanism == "Bromination":
        bromination_rule.edit(editor, substrate, reagent, site)
    elif mechanism == "Chlorination":
        chlorination_rule.edit(editor, substrate, reagent, site)
    elif mechanism in {"Hydrogenation", "Carbonyl hydrogenation"}:
        _order(editor, *maps[:2], 1)
        editor.GetBondBetweenAtoms(site[0], site[1]).SetStereo(Chem.BondStereo.STEREONONE)
        symbol = {"Bromination": "Br", "Chlorination": "Cl"}.get(mechanism, "H")
        introduced = [a.GetAtomMapNum() for a in reagent.GetAtoms() if a.GetSymbol() == symbol]
        _remove(editor, *introduced)
        for end, atom in zip(maps, introduced):
            _add(editor, end, atom)
    elif mechanism == "Hydration":
        hydration_rule.edit(editor, substrate, reagent, site)
    elif mechanism == "Hydrohalogenation":
        hydrohalogenation_rule.edit(editor, substrate, reagent, site)
    elif mechanism in {"Esterification", "Ester hydrolysis"}:
        carbon, _, old_oxygen = maps[:3]
        if mechanism == "Esterification":
            other_oxygen = reagent.GetAtomWithIdx(site[3]).GetAtomMapNum()
        else:
            other_oxygen = atom_of("O")
        h = _hydrogens(combined, other_oxygen)[0]
        _remove(editor, carbon, old_oxygen); _remove(editor, other_oxygen, h)
        _add(editor, carbon, other_oxygen); _add(editor, old_oxygen, h)
    elif mechanism == "Alcohol oxidation":
        carbon, oxygen = maps
        carbon_h = _hydrogens(combined, carbon)[0]; oxygen_h = _hydrogens(combined, oxygen)[0]
        oxidant_o, chlorine = atom_of("O"), atom_of("Cl")
        _remove(editor, carbon, carbon_h); _remove(editor, oxygen, oxygen_h)
        _remove(editor, oxidant_o, chlorine); _order(editor, carbon, oxygen, 2)
        _add(editor, oxidant_o, carbon_h); _add(editor, oxidant_o, oxygen_h)
        _charge(editor, oxidant_o, 0); _charge(editor, chlorine, -1)
        # Only this reactive tetrahedron becomes planar. Unaffected stereo is
        # not cleared and is independently checked by the exact edit contract.
        next(a for a in editor.GetAtoms() if a.GetAtomMapNum() == carbon).SetChiralTag(Chem.ChiralType.CHI_UNSPECIFIED)
    elif mechanism == "Aldehyde oxidation":
        carbon, _ = maps
        formyl_h = _hydrogens(combined, carbon)[0]
        oxidant_o, chlorine = atom_of("O"), atom_of("Cl")
        _remove(editor, carbon, formyl_h); _remove(editor, oxidant_o, chlorine)
        _add(editor, carbon, oxidant_o); _add(editor, oxidant_o, formyl_h)
        _charge(editor, oxidant_o, 0); _charge(editor, chlorine, -1)
    else:
        raise ValueError("Unsupported graph transformation.")
    after = _finish(editor)
    fragments = validate_products(combined, after, maps[0], mechanism == "Ester saponification")
    if mechanism in ester_rules.PATHWAYS:
        ester_rules.validate_cleavage(combined, after, substrate, site, reagent, mechanism)
    elif mechanism == "Hydrogenation":
        hydrogenation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Carbonyl hydrogenation":
        carbonyl_hydrogenation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Alcohol oxidation":
        if primary_alcohol_oxidation_rule.is_primary(substrate, site):
            primary_alcohol_oxidation_rule.validate(combined, after, substrate, reagent, site)
        elif secondary_alcohol_oxidation_rule.is_secondary(substrate,site):
            secondary_alcohol_oxidation_rule.validate(combined,after,substrate,reagent,site)
        else:
            alcohol_oxidation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Alcohol dehydration":
        alcohol_dehydration_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Alcohol substitution":
        alcohol_substitution_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "SN2":
        sn2_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "E2":
        e2_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "SN1":
        sn1_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "E1":
        e1_rule.validate(combined, after, substrate, site)
    elif mechanism == "Hydration":
        hydration_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Hydrohalogenation":
        hydrohalogenation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Bromination":
        bromination_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Chlorination":
        chlorination_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Epoxidation":
        epoxidation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Alkene dihydroxylation":
        dihydroxylation_rule.validate(combined, after, substrate, reagent, site, dihydroxylation_profile)
    elif mechanism == "Alkyne partial hydrogenation":
        alkyne_partial_hydrogenation_rule.validate(combined, after, substrate, reagent, site)
    elif mechanism == "Alkyne hydrogenation":
        alkyne_complete_hydrogenation_rule.validate(combined, after, substrate, [item["mol"] for item in inputs[1:]], site)
    elif mechanism == "Alkyne halogenation":
        alkyne_halogenation_rule.validate(combined, after, substrate, [item["mol"] for item in inputs[1:]], site,
                                         anti_model=inputs[0].get("alkyneHalogenAntiModel", False))
    elif mechanism == "Alkyne hydrohalogenation":
        alkyne_hydrohalogenation_rule.validate(combined, after, substrate, [item["mol"] for item in inputs[1:]], site)
    return fragments


def _fragment_outputs(fragments, main_name):
    """Combine an oxidant's disconnected counterions into its full salt product."""
    outputs = [{"name": main_name, "smiles": _identity(fragments[0]), "mappedSmiles": Chem.MolToSmiles(fragments[0])}]
    rest = fragments[1:]
    cation = next((f for f in rest if f.GetNumAtoms() == 1 and f.GetAtomWithIdx(0).GetFormalCharge() == 1), None)
    chloride = next((f for f in rest if f.GetNumAtoms() == 1 and f.GetAtomWithIdx(0).GetSymbol() == "Cl"
                     and f.GetAtomWithIdx(0).GetFormalCharge() == -1), None)
    if cation is not None and chloride is not None:
        salt = Chem.CombineMols(cation, chloride)
        symbol = cation.GetAtomWithIdx(0).GetSymbol()
        names = {"Na": "Sodium", "K": "Potassium", "Li": "Lithium", "Rb": "Rubidium", "Cs": "Caesium"}
        outputs.append({"name": names[symbol] + " chloride", "smiles": _identity(salt),
                        "mappedSmiles": Chem.MolToSmiles(salt), "formula": symbol + "Cl"})
        rest = [f for f in rest if f is not cation and f is not chloride]
    common = {"O": "Water", "Oc1ccccc1": "Phenol", "O=C=O": "Carbon dioxide", "[Br-]": "Bromide ion", "[Cl-]": "Chloride ion", "[I-]": "Iodide ion",
              "Cl": "Hydrogen chloride", "Br": "Hydrogen bromide", "I": "Hydrogen iodide"}
    for f in rest:
        smiles = _identity(f)
        fallback = "Carboxylic acid product" if graph.find_carboxylic_acids(f) else "Alcohol product" if graph.find_alcohols(f) else "Coproduct"
        outputs.append({"name": common.get(smiles, fallback), "smiles": smiles, "mappedSmiles": Chem.MolToSmiles(f)})
    return outputs


def generate_pair(first_id, second_id, catalog, product_names=None, *, conditions=None):
    """Return all supported mechanism/site candidates for a selected pair."""
    product_names = product_names or {}
    conditions = conditions or {}
    candidates, notes = [], []
    for substrate_id, reagent_id in ((first_id, second_id), (second_id, first_id)):
        substrate = Chem.MolFromSmiles(catalog[substrate_id]["smiles"])
        reagent = Chem.MolFromSmiles(catalog[reagent_id]["smiles"])
        role = reagent_role(reagent)
        bromination_sites = [(site, bromination_rule.assess(substrate, site)) for site in bromination_rule.sites(substrate)] if role == "halogen" and reagent.GetAtomWithIdx(0).GetSymbol() == "Br" else []
        chlorination_sites = [(site, chlorination_rule.assess(substrate, site)) for site in chlorination_rule.sites(substrate)] if role == "halogen" and reagent.GetAtomWithIdx(0).GetSymbol() == "Cl" else []
        epoxidation_sites, epoxidation_notes = epoxidation_rule.candidates(substrate, reagent) if role == "peroxyacid" else ([], [])
        notes.extend(epoxidation_notes)
        hydrohalogenation_sites = [(site, hydrohalogenation_rule.assess(substrate, reagent, site)) for site in hydrohalogenation_rule.sites(substrate)] if role == "hydrogen-halide" else []
        hydration_sites = [(site, hydration_rule.assess(substrate, site)) for site in hydration_rule.sites(substrate)] if role == "water" else []
        hydrogenation_sites = [(site, hydrogenation_rule.assess(substrate, site)) for site in graph.find_alkenes(substrate)] if role == "hydrogen" else []
        carbonyl_sites = [(site, carbonyl_hydrogenation_rule.assess(substrate, site)) for site in carbonyl_hydrogenation_rule.sites(substrate)] if role == "hydrogen" else []
        partial_alkyne_sites = [(site, alkyne_partial_hydrogenation_rule.assess(substrate, site)) for site in graph.find_alkynes(substrate)] if role == "hydrogen" else []
        complete_alkyne_sites = [(site, alkyne_complete_hydrogenation_rule.assess(substrate, site)) for site in graph.find_alkynes(substrate)] if role == "hydrogen" else []
        halogen_alkyne_sites = [(tuple(site) + (2 if conditions.get("additionStage") == "two" else 1,),
                                alkyne_halogenation_rule.assess(substrate, tuple(site) + (2 if conditions.get("additionStage") == "two" else 1,)))
                               for site in graph.find_alkynes(substrate)] if role == "halogen" else []
        hx_alkyne_sites = [(site, alkyne_hydrohalogenation_rule.assess(substrate, reagent, site))
                           for site in alkyne_hydrohalogenation_rule.sites(substrate, 2 if conditions.get("additionStage") == "two" else 1)] if role == "hydrogen-halide" else []
        oxidation_sites = [(site, (primary_alcohol_oxidation_rule if primary_alcohol_oxidation_rule.is_primary(substrate, site) else secondary_alcohol_oxidation_rule if secondary_alcohol_oxidation_rule.is_secondary(substrate,site) else alcohol_oxidation_rule).assess(substrate, site)) for site in alcohol_oxidation_rule.sites(substrate)] if role == "hypochlorite" else []
        substitution_sites = [(site, sn2_rule.assess(substrate, site)) for site in sn2_rule.sites(substrate)] if role == "hydroxide" else []
        elimination_sites = [(site, e2_rule.assess(substrate, site)) for site in e2_rule.sites(substrate)] if role == "hydroxide" else []
        solvolysis_sites = [(site, sn1_rule.assess(substrate, site)) for site in sn1_rule.sites(substrate)] if role == "water" else []
        unimolecular_sites = [(site, e1_rule.assess(substrate, site)) for site in e1_rule.sites(substrate)] if role == "water" else []
        dihydroxylation_profile = dihydroxylation_rule.r3.structural_reference(substrate, conditions) if role == 'hydrogen-peroxide' else None
        if role == 'hydrogen-peroxide' and conditions.get('temperature') == 'cooled':
            parent = Chem.MolToSmiles(substrate, isomericSmiles=False)
            if parent == 'O=C(O)C=CC(=O)O':
                notes.append('The fumaric-acid cold source experiment also forms oxalic acid and recovers calcium salts. A single neutral tartaric-acid product would omit validated competing oxidation and salt isolation; this endpoint is not implemented. Maleic acid was not a 0 C example.')
            elif dihydroxylation_profile is None and any(m.workup and m.substrate == parent for m in dihydroxylation_rule.r3.MODELS.values()):
                if dihydroxylation_rule.r3.identity(substrate) != parent:
                    notes.append('The R3 acid source profile does not establish the specified E/Z or tetrahedral outcome. Specified stereochemistry is not discarded to fit an unconfigured source reference.')
                else:
                    notes.append('This source-parent acid has an R3 reference, but the selected named profile ID/version conflicts. Clear the stale reference and review the matching source profile; no implicit fallback is allowed.')
        dihydroxylation_sites = [(site, dihydroxylation_rule.assess(substrate, site, dihydroxylation_profile)) for site in dihydroxylation_rule.sites(substrate, dihydroxylation_profile)] if role == "hydrogen-peroxide" else []
        dehydration_sites = [(site, alcohol_dehydration_rule.assess(substrate, site)) for site in alcohol_dehydration_rule.sites(substrate)] if role == "sulfuric-acid" else []
        # Mixed pi/alcohol systems remain with the existing HX-addition
        # assessors. They are not new alcohol-substitution permissions or new
        # diagnostics for those unrelated consumers.
        alcohol_hx_sites = [(site, alcohol_substitution_rule.assess(substrate, reagent, site)) for site in alcohol_substitution_rule.sites(substrate)] if role == "hydrogen-halide" and not graph.find_alkenes(substrate) and not graph.find_alkynes(substrate) else []
        if role is None and alcohol_substitution_rule.sites(substrate) and (
                reagent.HasSubstructMatch(Chem.MolFromSmarts('[P](-[Br])(-[Br])-[Br]'))
                or reagent.HasSubstructMatch(Chem.MolFromSmarts('[S](=[O])(-[Cl])-[Cl]'))
                or (reagent.GetNumAtoms() == 1 and reagent.GetAtomWithIdx(0).GetSymbol() in {'F', 'Cl', 'Br', 'I'})):
            notes.append("Alcohol substitution needs actual neutral HX activation and its consumed halide. Bare halide/HF and alternative PBr3/SOCl2 activating systems are not implemented; no unactivated OH displacement or HX coproducts are inferred.")
        if role is None and sn1_rule.sites(substrate) and graph.find_alcohols(reagent):
            notes.append("SN1 in this model uses actual water capture; alcohol trapping solvents/nucleophiles such as methanol are not enabled. This is a reagent-model limitation, not proof that alcohol solvolysis is impossible.")
        issue = scope_issue(substrate, {"C", "H", "O", "Cl", "Br", "I"}, allow_stereo=True)
        specified_centers = any(a.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED for a in substrate.GetAtoms())
        if issue:
            notes.extend(r["message"] for _, report in alcohol_hx_sites for r in report["rejections"])
            notes.extend(r["message"] for _, report in dehydration_sites for r in report["rejections"])
            notes.extend(r["message"] for _, report in partial_alkyne_sites for r in report["rejections"])
            notes.extend(r["message"] for _, report in complete_alkyne_sites for r in report["rejections"])
            notes.extend(r["message"] for _, report in halogen_alkyne_sites for r in report["rejections"])
            notes.extend(r["message"] for _, report in hx_alkyne_sites for r in report["rejections"])
            if hydrogenation_sites or carbonyl_sites or oxidation_sites or substitution_sites or elimination_sites or solvolysis_sites or unimolecular_sites or hydration_sites or hydrohalogenation_sites or bromination_sites or chlorination_sites:
                notes.extend(r["message"] for _, report in [*hydrogenation_sites, *carbonyl_sites, *oxidation_sites, *substitution_sites, *elimination_sites, *solvolysis_sites, *unimolecular_sites, *hydration_sites, *hydrohalogenation_sites, *bromination_sites, *chlorination_sites] for r in report["rejections"])
            elif any(a.GetAtomicNum() == 6 for a in substrate.GetAtoms()): notes.append(issue)
            continue
        plans = []
        def plan(mechanism, family, site, profile, description, source, extra="", *, compatibility=None):
            if (specified_centers and mechanism != "SN2" and mechanism not in ester_rules.PATHWAYS
                    and not (mechanism in {"Hydrogenation", "Carbonyl hydrogenation", "Alcohol oxidation", "Alcohol dehydration", "Alcohol substitution", "E2", "SN1", "E1", "Hydration", "Hydrohalogenation", "Bromination", "Chlorination", "Epoxidation", "Alkene dihydroxylation", "Alkyne partial hydrogenation", "Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"} and compatibility and compatibility["eligible"])):
                notes.append(f"Specified tetrahedral stereochemistry is not validated for {mechanism}; no configuration is discarded.")
                return
            plans.append((mechanism, family, tuple(site), profile, description, source, extra, compatibility))
        extended_reaction_rules.candidates(substrate, reagent, role, conditions, plan, notes)
        for site, report in alcohol_hx_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Alcohol substitution", "Substitution", site,
                 {"temperature": "heated" if report["alcoholClass"] in {"methyl", "primary"} else "ambient"},
                 "Actual " + report["hydrogenHalide"] + " activates the selected OH as water and supplies the incoming halogen. This is a balanced net option, not bare OH displacement.",
                 alcohol_substitution_rule.SOURCE,
                 "HX is consumed, not a catalyst. Primary SN2-type, tertiary SN1-type and unresolved secondary/benzylic cases are distinguished. No complete mapped activation mechanism, universal inversion, rearranged capture, product ratios or experimental site selectivity is asserted.", compatibility=report)
        if role == "sulfuric-acid":
            if graph.find_alcohols(substrate) and not dehydration_sites:
                for alcohol in graph.find_alcohols(substrate):
                    environment_issue = alcohol_dehydration_rule.site_issue(substrate, alcohol)
                    if environment_issue: notes.append(environment_issue)
                notes.append("Alcohol dehydration needs an actual beta C–H; methanol and beta-H-free sites cannot lose an invented hydrogen.")
            for site, report in dehydration_sites:
                if not report["eligible"]:
                    notes.extend(r["message"] for r in report["rejections"]); continue
                plan("Alcohol dehydration", "Elimination", site, {"catalyst": "acid", "temperature": "heated"},
                     "Selected OH and beta H form one formal net water coproduct as C=C forms. Distinct constitutional beta products are alternatives, not a major/minor prediction.",
                     alcohol_dehydration_rule.SOURCE, alcohol_dehydration_rule.LIMITATION, compatibility=report)
        elif graph.find_alcohols(substrate) and reagent.HasSubstructMatch(Chem.MolFromSmarts("P(=O)(O)(O)O")):
            notes.append("Alcohol dehydration currently validates the existing actual sulfuric-acid model only; phosphoric-acid activation is not implemented, not chemically impossible.")
        for site, report in hx_alkyne_sites:
            if catalog[substrate_id].get("alkyneHxStereoIssue"):
                notes.append(catalog[substrate_id]["alkyneHxStereoIssue"]); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Alkyne hydrohalogenation", "Addition", site,
                 {"additionStage": "two" if site[3] == 2 else "one", "solvent": "dry", "temperature": "ambient"},
                 "Actual selected HX supplies H and halogen at this isolated C≡C. Terminal Markovnikov orientation is bounded; inequivalent internal orientations are separate constitutional alternatives, not a major/minor prediction. Two equivalents give a geminal dihalide without moving the carbon skeleton.",
                 alkyne_hydrohalogenation_rule.SOURCE, alkyne_hydrohalogenation_rule.LIMITATION, compatibility=report)
        for site, report in halogen_alkyne_sites:
            if catalog[substrate_id].get("alkyneHalogenStereoIssue"):
                notes.append(catalog[substrate_id]["alkyneHalogenStereoIssue"]); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Alkyne halogenation", "Addition", site, {"solvent": "dry", "additionStage": "two" if site[2] == 2 else "one"},
                 "The selected isolated acyclic C≡C receives the actual chosen X2: one equivalent gives a vicinal dihaloalkene; two give a 1,1,2,2-tetrahaloalkane. Br2 first-stage anti geometry is independently CIP-checked; Cl2 first-stage E/Z remains unassigned.",
                 alkyne_halogenation_rule.SOURCE, alkyne_halogenation_rule.LIMITATION, compatibility=report)
        for site, report in complete_alkyne_sites:
            if catalog[substrate_id].get("alkyneCompleteStereoIssue"):
                notes.append(catalog[substrate_id]["alkyneCompleteStereoIssue"]); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Alkyne hydrogenation", "Reduction", site, {"catalyst": "metal"},
                 "Two actual H2 equivalents fully saturate the selected isolated acyclic C≡C to C–C, adding two H to each carbon. Screened remote OH/ethers and applicable distant configurations are checked for retention.",
                 alkyne_complete_hydrogenation_rule.SOURCE, alkyne_complete_hydrogenation_rule.LIMITATION, compatibility=report)
        for site, report in partial_alkyne_sites:
            if catalog[substrate_id].get("alkynePartialStereoIssue"):
                notes.append(catalog[substrate_id]["alkynePartialStereoIssue"]); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Alkyne partial hydrogenation", "Reduction", site, {"catalyst": "lindlar"},
                 "One actual H2 reduces the selected isolated acyclic C≡C to C=C. Net syn addition gives cis/Z for an internal alkyne; terminal products have no E/Z assignment.",
                 alkyne_partial_hydrogenation_rule.SOURCE, alkyne_partial_hydrogenation_rule.LIMITATION, compatibility=report)
        for site, report in dihydroxylation_sites:
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"].replace("Hydration", "Dihydroxylation")); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            release_profile = {"catalyst": "osmium", "workup": "aqueous-release"}
            if conditions.get('conditionProfileId') == dihydroxylation_profile and dihydroxylation_profile:
                if not dihydroxylation_rule.r3.MODELS[dihydroxylation_profile].workup:
                    release_profile = {"catalyst": "osmium"}
            source_reference = bool(dihydroxylation_profile and (conditions.get('conditionProfileId') == dihydroxylation_profile
                or dihydroxylation_rule.r3.MODELS[dihydroxylation_profile].workup))
            plan("Alkene dihydroxylation", "Oxidation", site, release_profile,
                 "The selected C=C receives two same-face OH groups in the catalytic Os/H2O2 net model. Starting geometry determines validated relative configurations; opposite faces are alternatives without ratios.",
                 dihydroxylation_rule.r3.SOURCE if source_reference else dihydroxylation_rule.SOURCE,
                 ('Exact source-parent free-product net reference; catalyst/recovery species are not mapped, and unspecified stereocenters remain unassigned. No predicted conversion, isolated purity, yield or mixtures.' if source_reference else dihydroxylation_rule.LIMITATION), compatibility=report)
        for ends, report in hydrogenation_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            plan("Hydrogenation", "Addition", ends, {"catalyst": "metal"},
                 "One H₂ adds at the selected isolated C=C. Screened remote aliphatic alcohols and applicable distant specified configurations are retained by the mapped edit; other isolated C=C sites are separate net options.",
                 hydrogenation_rule.SOURCE,
                 "One-site net transformation, not a prediction of selective partial conversion. New stereocenters, syn face selection, epimerization, competing reductions and catalyst-specific outcomes are not assigned.", compatibility=report)
        for site, report in carbonyl_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            plan("Carbonyl hydrogenation", "Reduction", site, {"catalyst": "metal"},
                 "One H₂ reduces the selected aldehyde/ketone C=O to C–OH. Its original oxygen and carbon skeleton, screened spectators and applicable distant specified configurations are retained in the mapped net edit.",
                 carbonyl_hydrogenation_rule.SOURCE,
                 "One-site net option, not selective partial conversion or a catalyst-specific protocol. New alcohol stereocenters remain unassigned; epimerization, ring reduction, benzylic deoxygenation and other competing outcomes are not predicted.", compatibility=report)
        for site, report in oxidation_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            primary = alcohol_oxidation_rule.classification(substrate, site) == "primary"
            if primary and conditions.get("oxidationStage") == "further":
                notes.append("Further oxidation starts from an aldehyde. Select the first alcohol oxidation stage first; no direct alcohol-to-acid product is generated.")
                continue
            plan("Alcohol oxidation", "Oxidation", site, {"solvent": "aqueous-protic"},
                 "The selected primary alcohol becomes an aldehyde at this net oxidation stage; further oxidation may occur and stopping at the aldehyde is not predicted." if primary else
                 "The selected secondary alcohol becomes a ketone; hypochlorite is reduced to chloride in the balanced net equation.",
                 alcohol_oxidation_rule.SOURCE,
                 "One hypochlorite formula unit per selected alcohol is a net oxidation stage, not a claim of an isolated product or selective mono-oxidation. Reagent-specific catalysis, pH, further oxidation and side reactions are not predicted. Do not mix household chemicals.", compatibility=report)
        if role == "hypochlorite" and not oxidation_sites and not graph.find_aldehydes(substrate):
            notes.append("No neutral saturated alcohol C–OH oxidation site was found; phenols, ethers, acids and ketones are not primary/secondary alcohol sites in this pathway.")
        for site, report in substitution_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            plan("SN2", "Substitution", site, {"solvent": "polar-aprotic"},
                 "The actual OH⁻ oxygen replaces the selected Cl/Br/I with backside inversion at a specified reacting center. Unaffected mapped configurations and screened groups are checked; unspecified centers remain unassigned.",
                 sn2_rule.SOURCE,
                 "One-site net substitution, not selective mono-substitution or an experimental efficiency prediction. Secondary/benzylic substrates and hydroxide can compete with elimination or other pathways; alcohol proton equilibria and intramolecular chemistry are not generally predicted.", compatibility=report)
        if role == "hydroxide" and not substitution_sites:
            notes.append("SN2 requires a supported single C(sp³)–Cl/Br/I bond; aryl/vinyl halides, fluoride and other leaving-group families are not enabled.")
        for site, report in elimination_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            plan("E2", "Elimination", site, {"solvent": "ethanolic-protic", "temperature": "heated"},
                 "Hydroxide accepts an actual selected beta H while C–H/C–X break and C=C forms in one concerted step. Screened spectators and distant configurations are checked; constitutional alternatives are separate options.",
                 e2_rule.SOURCE,
                 "Acyclic anti model only: ring-bound elimination is not enabled. E/Z is assigned only from two specified local tetrahedra with a unique beta H; other outcomes stay unassigned. One-site net options do not predict selectivity, ratios, rates or yields; hydroxide can also substitute or deprotonate.", compatibility=report)
        if role == "hydroxide" and not elimination_sites and graph.find_alkyl_halides(substrate):
            notes.append("E2 has no eligible beta carbon with an actual C–H bond next to this alkyl-halide site; methyl/no-beta-H substrates cannot use this elimination model.")
        for site, report in solvolysis_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            plan("SN1", "Substitution", site, {"solvent": "aqueous-protic", "temperature": "ambient"},
                 "The screened C–Cl/Br/I ionizes to a mapped positive planar carbocation, then actual water attacks and solvent water removes a proton in a separate step. Only reacting-center configuration is lost; distant configurations are checked.",
                 sn1_rule.SOURCE,
                 "Water-only one-site solvolysis model: ion-pair facial preference, racemization ratio, rearrangements, E1/SN2 competition and selective mono-conversion are not predicted. Net HX reports released acid; the aqueous mechanism explicitly shows hydronium plus halide, not undissociated HX.", compatibility=report)
        if role == "water" and not solvolysis_sites and any(a.GetSymbol() in {"Cl", "Br", "I", "F"} for a in substrate.GetAtoms()):
            notes.append("SN1 needs a supported carbocation-forming C(sp³)–Cl/Br/I site; aryl/vinyl halides, fluoride and new leaving groups are not enabled.")
        for site, report in unimolecular_sites:
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            e1_rule.water_oxygen(Chem.AddHs(reagent))
            plan("E1", "Elimination", site, {"solvent": "aqueous-protic", "temperature": "heated"},
                 "C–X ionizes to a positive planar carbocation before actual solvent water removes the selected saturated beta H and C=C forms. Other beta positions are separate net options; distant mapped configurations are checked.",
                 e1_rule.SOURCE,
                 "Water-only one-site unrearranged E1 model. SN1, hydride/alkyl shifts, ion pairs, cyclization and selective mono-conversion are not predicted; absence of an SN1 option is not evidence that substitution cannot occur. All new E/Z remains unassigned: no anti-E2, Zaitsev/Hofmann ratios or guaranteed major product. Net HX reports released acid; the aqueous mechanism shows hydronium plus halide.", compatibility=report)
        if role == "water":
            for halide in graph.find_alkyl_halides(substrate):
                if not any(site[:2] == halide for site, _ in unimolecular_sites):
                    notes.append(e1_rule.cation_issue(substrate, halide) or "This E1 site has no eligible saturated beta C–H; aromatic/sp2 beta loss and cumulated products are not enabled.")
        elif role is None and graph.find_alkyl_halides(substrate) and graph.find_alcohols(reagent):
            notes.append("E1 in this model uses actual solvent water; alcohol trapping/base systems are not enabled. This is a reagent-model limitation, not chemical impossibility.")
        for site, report in hydration_sites:
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"])
                continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            basis = report["orientationBasis"]
            plan("Hydration", "Addition", site, {"catalyst": "acid"},
                 "Water adds H/OH at the selected C=C; OH capture uses " + basis + ". Other sites and screened spectators are unchanged only in this net option.",
                 hydration_rule.SOURCE,
                 "Acid activation is required and the catalyst is regenerated, not consumed. Initial water-capture connectivity only: migration, isomerization, polymerization, further hydration and experimental selectivity are not predicted. Ambiguous orientations are separate alternatives, not major/minor ratios. Water H maps are net bookkeeping, not an isotope/proton-exchange mechanism. New stereocenters and syn/anti outcomes remain unassigned; a generated 3D conformer is not a stereochemical prediction.",
                 compatibility=report)
        for site, report in hydrohalogenation_sites:
            # Reuse only the existing raw-direction preservation flag, not
            # hydration's chemical orientation or spectator policy.
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"].replace("Hydration", "Ionic HX addition"))
                continue
            issue = hydrohalogenation_rule.context_issue(conditions)
            if issue:
                notes.append(issue)
                continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"])
                continue
            oxygen_spectators = any(g["type"] in {"alcohol", "ether"} and g["disposition"] == "preserved" for g in report["groups"])
            if oxygen_spectators and conditions.get("temperature") == "heated":
                notes.append("Heated HCl with oxygen groups is outside the bounded ambient spectator model; competing C–O chemistry/condition-dependent selectivity is not validated, not declared impossible.")
                continue
            plan("Hydrohalogenation", "Addition", site, {"temperature": "ambient"} if oxygen_spectators else {},
                 "The actual " + report["hydrogenHalide"] + " supplies both H and halogen at this selected C=C using " + report["orientationBasis"] + ".",
                 hydrohalogenation_rule.SOURCE,
                 "Ionic unrearranged net capture only: HX is consumed, not an acid catalyst. No radical/peroxide anti-Markovnikov pathway, product ratios, rates, yields or selective mono-addition are predicted. Adjacent shifts and short capture risks are screened; longer-range migration, polymerization and further addition are not predicted. Screened oxygen retention is qualified ambient HCl only, not inertness or a substitution/cleavage protocol. New configurations and syn/anti remain unassigned; one conformer is not a stereochemical outcome.",
                 compatibility=report)
        if role is None and graph.find_alkenes(substrate) and reagent.GetNumAtoms() == 1 and reagent.GetAtomWithIdx(0).GetSymbol() == "F":
            notes.append("HF is outside the validated ionic alkene hydrohalogenation reagent model; choose actual neutral HCl, HBr or HI. No alkene product is inferred from fluoride identity alone.")
        for site in epoxidation_sites:
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"].replace("Hydration", "Epoxidation")); continue
            issue = epoxidation_rule.context_issue(conditions)
            if issue:
                notes.append(issue); continue
            report = epoxidation_rule.assess(substrate, site)
            plan("Epoxidation", "Addition", site, {"solvent": "dry"},
                 "The actual peroxyacid terminal oxygen bridges the selected C=C in one concerted same-face transfer. Its carbonyl oxygen accepts the peracid H while the proximal oxygen becomes the acid carbonyl.",
                 epoxidation_rule.SOURCE,
                 "One conditional oxygen-transfer option, not selective mono-epoxidation or an experimental protocol. Specified starting geometry determines local configurations; unknown geometry remains unsigned. The acid coproduct may enable later ring opening, which is not predicted. Opposite approach faces have no assigned ratio.",
                 compatibility=report)
        for site, report in bromination_sites:
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"].replace("Hydration", "Bromination"))
                continue
            issue = bromination_rule.context_issue(conditions)
            if issue:
                notes.append(issue); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Bromination", "Addition", site, {"solvent": "dry"},
                 "One actual Br2 supplies one Br to each selected C=C carbon. Validated starting geometry determines local anti alternatives; unspecified internal geometry is not guessed.",
                 bromination_rule.SOURCE,
                 "Conditional neutral non-nucleophilic net model only. Water/alcohol capture, intramolecular cyclization, radical substitution, added activation and experimental selectivity are not equivalent dibromination pathways. Opposite-face structures are separate alternatives without ratios; a meso product is not duplicated. Anti is addition geometry, not a universal trans product label. No complete bromonium mechanism is implemented.",
                 compatibility=report)
        for site, report in chlorination_sites:
            if catalog[substrate_id].get("hydrationStereoIssue"):
                notes.append(catalog[substrate_id]["hydrationStereoIssue"].replace("Hydration", "Chlorination"))
                continue
            issue = chlorination_rule.context_issue(conditions)
            if issue:
                notes.append(issue); continue
            if not report["eligible"]:
                notes.extend(r["message"] for r in report["rejections"]); continue
            plan("Chlorination", "Addition", site, {"solvent": "dry"},
                 "One actual Cl2 supplies one Cl to each selected C=C carbon. Validated starting geometry determines local anti alternatives; unspecified internal geometry is not guessed.",
                 chlorination_rule.SOURCE,
                 "Conditional neutral non-nucleophilic net model only. Water/alcohol capture, intramolecular cyclization, radical substitution, added activation and experimental selectivity are not equivalent dichlorination pathways. Opposite-face structures are separate alternatives without ratios; a meso product is not duplicated. Anti is addition geometry, not a universal trans product label. No complete chloronium mechanism is implemented.",
                 compatibility=report)
        # Bounded oxygen chemistry: carbon skeletons, aromatic spectators and
        # repeated supported groups are allowed; unrelated heteroatom chemistry isn't.
        oxygen_scope = all(a.GetSymbol() in {"C", "H", "O"} for a in substrate.GetAtoms())
        if oxygen_scope and role == "hypochlorite" and not graph.find_alkenes(substrate) and not graph.find_alkynes(substrate):
            aldehydes = graph.find_aldehydes(substrate)
            if aldehydes and conditions.get("oxidationStage") == "further" and conditions.get("solvent") == "aqueous-protic":
                for site in aldehydes:
                    plan("Aldehyde oxidation", "Oxidation", site,
                         {"solvent": "aqueous-protic", "oxidationStage": "further"},
                         "The selected aldehyde becomes a carboxylic acid reporting structure in the aqueous further-oxidation net model. Ketones do not match this rule.", SOURCES["aldehyde"],
                         "Neutral acid reporting form only: solution protonation, reagent-specific isolation and side reactions are not predicted. Not a laboratory procedure; never mix household chemicals.")
            elif aldehydes:
                assessment = aldehyde_oxidation_conditions.assess_conditions({}, conditions)
                notes.append(assessment['note'] + ' Select Further oxidation and Water / polar protic to inspect the existing reporting graph; no isolated acid or new medium profile is inferred.')
        acids = graph.find_carboxylic_acids(substrate)
        alcohols = graph.find_alcohols(reagent)
        if oxygen_scope and acids and not scope_issue(reagent, {"C", "H", "O"}):
            for acid in acids:
                for c, o in alcohols:
                    if graph.substitution_degree(reagent.GetAtomWithIdx(c)) >= 3:
                        notes.append("Tertiary alcohol esterification has competing dehydration pathways outside this model."); continue
                    plan("Esterification", "Condensation", (*acid, o), {"catalyst": "acid"},
                         "The selected acid acyl carbon bonds to the selected alcohol oxygen; the acid OH and alcohol H form water. Other functional groups remain unchanged in this one-site net pathway.", SOURCES["ester"])
        if oxygen_scope and role == "water":
            for site in graph.find_esters(substrate):
                issue = ester_rules.site_issue(substrate, site)
                if issue:
                    notes.append(issue); continue
                cyclic = substrate.GetBondBetweenAtoms(site[0], site[2]).IsInRing()
                plan("Ester hydrolysis", "Hydrolysis", site, {"solvent": "aqueous-protic", "catalyst": "acid"},
                     "Acid-catalyzed water addition opens the selected lactone acyl–O bond to give one connected hydroxy carboxylic acid. This pathway is reversible." if cyclic else
                     "Acid-catalyzed water addition cleaves the selected ester acyl–O bond to give its carboxylic acid and alcohol or phenol. This pathway is reversible.", SOURCES["ester"],
                     "One-site acyl-cleavage net model; epimerization, competing cleavage and equilibrium composition are not predicted.")
        if acids and graph.find_amines(reagent):
            notes.append("Acid–amine amidation is not implemented; initial salt formation and dehydration require distinct rules.")
        seen_e1_products = set()
        seen_hydration_products = set()
        seen_hydrohalogenation_products = []
        seen_bromination_products = []
        seen_chlorination_products = []
        seen_epoxidation_products = []
        seen_dihydroxylation_products = []
        for mechanism, family, site, profile, description, source, extra, compatibility in plans:
            equation_ids = extended_reaction_rules.equation_ids(mechanism, substrate_id, reagent_id, site) or ([substrate_id] if mechanism == "E1" else [substrate_id, reagent_id])
            inputs, next_map = [], 1
            for identifier in equation_ids:
                item, next_map = _species(identifier, catalog[identifier], next_map); inputs.append(item)
            if mechanism == "Alkyne halogenation":
                inputs[0]["alkyneHalogenAntiModel"] = (conditions.get("solvent") == "dry"
                    and conditions.get("additionStage") == "one" and conditions.get("catalyst") in {None, "", "none"}
                    and conditions.get("temperature") != "heated")
            try:
                fragments = transform(mechanism, inputs, site, dihydroxylation_profile=dihydroxylation_profile if mechanism == 'Alkene dihydroxylation' else None)
                smiles = _identity(fragments[0])
                if mechanism == "Alkene dihydroxylation":
                    equivalent = next((old for old in seen_dihydroxylation_products if old["productSmiles"] == smiles
                                       and dihydroxylation_rule.equivalent_sites(substrate, old["site"]["substrateAtoms"], site)), None)
                    if equivalent:
                        equivalent["site"]["parameters"]["equivalentSiteFaces"].append([inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]] + [site[2]])
                        continue
                if mechanism == "E1":
                    key = (site[:2], smiles)
                    if key in seen_e1_products: continue
                    seen_e1_products.add(key)  # Other C–X identities remain distinct options.
                if mechanism == "Hydration":
                    key = (frozenset(site[:2]), smiles)
                    if key in seen_hydration_products: continue
                    seen_hydration_products.add(key)  # Keep distinct C=C identities selectable.
                if mechanism == "Bromination":
                    equivalent = next((old for old in seen_bromination_products if old["productSmiles"] == smiles
                                       and bromination_rule.equivalent_sites(substrate, old["site"]["substrateAtoms"], site)), None)
                    if equivalent:
                        equivalent["site"]["parameters"]["equivalentSiteFaces"].append([inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]] + [site[2]])
                        continue
                if mechanism == "Chlorination":
                    equivalent = next((old for old in seen_chlorination_products if old["productSmiles"] == smiles
                                       and chlorination_rule.equivalent_sites(substrate, old["site"]["substrateAtoms"], site)), None)
                    if equivalent:
                        equivalent["site"]["parameters"]["equivalentSiteFaces"].append([inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]] + [site[2]])
                        continue
                if mechanism == "Epoxidation":
                    equivalent = next((old for old in seen_epoxidation_products if old["productSmiles"] == smiles
                                       and epoxidation_rule.equivalent_sites(substrate, old["site"]["substrateAtoms"], site)), None)
                    if equivalent:
                        equivalent["site"]["parameters"]["equivalentSiteFaces"].append([inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:2]] + [site[2]])
                        continue
                if mechanism == "Hydrohalogenation":
                    equivalent = next((old for old in seen_hydrohalogenation_products if old["productSmiles"] == smiles
                                       and hydrohalogenation_rule.equivalent_sites(substrate, old["site"]["substrateAtoms"], site)), None)
                    if equivalent:
                        aliases = equivalent["site"]["parameters"]["equivalentSiteAtomMaps"]
                        aliases.append([inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site])
                        continue
                hydrogenation_name = "Partially hydrogenated product" if graph.find_alkenes(fragments[0]) else "Alkane product"
                if mechanism == "Hydrogenation" and not graph.find_alkenes(fragments[0]) and graph.find_alcohols(fragments[0]):
                    hydrogenation_name = "Hydrogenated alcohol product"
                name = product_names.get(smiles, {"SN1": "Alcohol product", "SN2": "Alcohol product", "Hydrogenation": hydrogenation_name,
                         "Esterification": "Ester product", "Ester hydrolysis": "Carboxylic acid product", "Alcohol oxidation": "Carbonyl product",
                         "Bromination": "Dibromide product", "Chlorination": "Dichloride product", "Carbonyl hydrogenation": "Alcohol product", "Hydration": "Alcohol product", "Hydrohalogenation": "Haloalkane product", "Aldehyde oxidation": "Carboxylic acid product", "Epoxidation": "Epoxide product",
                         "Alcohol dehydration": "Alkene product", "Alcohol substitution": "Haloalkane product", "Ester saponification": "Carboxylate ion",
                         "Alkyne hydrogenation": "Hydrogenated product", "Alkyne partial hydrogenation": "Alkene product", "Alkyne halogenation": "Halogenated product",
                         "Alkyne hydrohalogenation": "Hydrohalogenated product", "Alkene dihydroxylation": "Diol product", "Polymerization model": "Finite phenyl-ended oligomer"}.get(mechanism, "Organic product"))
                # Naming is downstream of validated graph generation. Preserve
                # reviewed identity names and the explicit partial-reduction
                # qualifier; neither names nor formulas affect eligibility.
                if smiles not in product_names and name != "Partially hydrogenated product":
                    name = simple_product_name(smiles) or name
                outputs = _fragment_outputs(fragments, name)
                for output in outputs[1:]:
                    output["name"] = product_names.get(output["smiles"], simple_product_name(output["smiles"]) or output["name"])
                if mechanism == "E2":
                    outputs = [outputs[0], *sorted(outputs[1:], key=lambda out: out["smiles"] != "O")]
            except (ValueError, RuntimeError, StopIteration, IndexError) as exc:
                if mechanism == "Alkyne hydrogenation":
                    notes.append(f"Complete alkyne hydrogenation at atoms {', '.join(str(i + 1) for i in site)} failed site/product/stereochemistry validation: {exc}")
                    continue
                notes.append(f"{mechanism} at substrate atoms {', '.join(str(i + 1) for i in site)} failed validation (site/product): {exc}" if mechanism in {"Alcohol dehydration", "Hydrogenation", "Carbonyl hydrogenation", "Alcohol oxidation", "SN2", "E2", "SN1", "E1", "Hydration", "Hydrohalogenation", "Bromination", "Chlorination", "Epoxidation"} else
                             "This structural case is not currently supported: its product failed validation."); continue
            site_maps = [inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:3 if mechanism in {"E1", "E2", "Alcohol dehydration"} else 2]]
            if mechanism == "Esterification":
                site_maps = [inputs[0]["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum(),
                             inputs[0]["mol"].GetAtomWithIdx(site[2]).GetAtomMapNum(),
                             inputs[1]["mol"].GetAtomWithIdx(site[3]).GetAtomMapNum()]
            elif mechanism in {"Ester hydrolysis", "Ester saponification"}:
                site_maps = [inputs[0]["mol"].GetAtomWithIdx(site[0]).GetAtomMapNum(),
                             inputs[0]["mol"].GetAtomWithIdx(site[2]).GetAtomMapNum(),
                             next(a.GetAtomMapNum() for a in inputs[1]["mol"].GetAtoms() if a.GetSymbol() == "O")]
            elif mechanism == "Polymerization model":
                site_maps = [item["mol"].GetAtomWithIdx(i).GetAtomMapNum() for item in inputs[:-1] for i in site[:2]]
            condition_names = {"acid": "acid catalyst", "metal": "suitable metal catalyst", "polar-aprotic": "polar aprotic medium",
                               "aqueous-protic": "aqueous protic medium", "ethanolic-protic": "ethanolic protic medium",
                               "ambient": "room temperature", "heated": "heated conditions", "dry": "dry medium"}
            condition_names["further"] = "explicit further-oxidation stage"
            condition_names["aqueous-release"] = "aqueous diol release (net assumption, not mapped work-up)"
            condition_names.update({"lindlar": "Lindlar catalyst", "osmium": "Os-based catalytic dihydroxylation system", "radical": "radical initiation model",
                                    "one": "one addition equivalent", "two": "two addition equivalents", "2": "two monomer units", "4": "four monomer units", "6": "six monomer units"})
            requirements = ", ".join(condition_names[value] for value in profile.values()) or "No additional conditions evaluated"
            parameters = {}
            graph_site = list(site)
            if mechanism == "Bromination":
                parameters.update(bromination_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
                parameters["faceAlternative"] = site[2]
                parameters["equivalentSiteFaces"] = [parameters["alkene"] + [site[2]]]
            elif mechanism == "Alkyne partial hydrogenation":
                parameters.update(alkyne_partial_hydrogenation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
            elif mechanism == "Alkyne hydrogenation":
                parameters.update(alkyne_complete_hydrogenation_rule.participants(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site))
            elif mechanism == "Alkyne halogenation":
                parameters.update(alkyne_halogenation_rule.participants(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site))
            elif mechanism == "Alkyne hydrohalogenation":
                parameters.update(alkyne_hydrohalogenation_rule.participants(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site))
                parameters["equivalentSiteAtomMaps"] = [[inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site[:3]]]
            elif mechanism == "Chlorination":
                parameters.update(chlorination_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
                parameters["faceAlternative"] = site[2]
                parameters["equivalentSiteFaces"] = [parameters["alkene"] + [site[2]]]
            elif mechanism == "Epoxidation":
                parameters.update(epoxidation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
                parameters["faceAlternative"] = site[2]
                parameters["equivalentSiteFaces"] = [parameters["alkene"] + [site[2]]]
            elif mechanism == "Alkene dihydroxylation":
                parameters.update(dihydroxylation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site))
                parameters["faceAlternative"] = site[2]
                parameters["equivalentSiteFaces"] = [parameters["alkene"] + [site[2]]]
            elif mechanism == "Hydrohalogenation":
                participants = hydrohalogenation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)
                parameters.update({k: v for k, v in participants.items() if k != "alkene"})
                parameters["equivalentSiteAtomMaps"] = [[inputs[0]["mol"].GetAtomWithIdx(i).GetAtomMapNum() for i in site]]
            elif mechanism == "Hydration":
                participants = hydration_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)
                parameters.update({k: v for k, v in participants.items() if k != "alkene"})
            elif mechanism == "E2":
                participants = e2_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)
                parameters["betaHydrogenMap"] = participants["hydrogen"]
                parameters["betaHydrogenMaps"] = sorted(n.GetAtomMapNum() for n in inputs[0]["mol"].GetAtomWithIdx(site[2]).GetNeighbors() if n.GetAtomicNum() == 1)
            elif mechanism == "E1":
                participants = e1_rule.participants(inputs[0]["mol"], site)
                parameters["betaHydrogenMap"] = participants["hydrogen"]
                parameters["betaHydrogenMaps"] = sorted(n.GetAtomMapNum() for n in inputs[0]["mol"].GetAtomWithIdx(site[2]).GetNeighbors() if n.GetAtomicNum() == 1)
            if mechanism in {"Alkyne halogenation", "Alkyne hydrohalogenation"}:
                parameters["equivalents"] = site[-1]; graph_site = list(site[:-1])
            elif mechanism == "Polymerization model":
                parameters["monomerUnits"] = site[2]; graph_site = list(site[:2])
            compatibility_rule = alcohol_substitution_rule if mechanism == "Alcohol substitution" else alcohol_dehydration_rule if mechanism == "Alcohol dehydration" else alkyne_hydrohalogenation_rule if mechanism == "Alkyne hydrohalogenation" else alkyne_halogenation_rule if mechanism == "Alkyne halogenation" else alkyne_complete_hydrogenation_rule if mechanism == "Alkyne hydrogenation" else alkyne_partial_hydrogenation_rule if mechanism == "Alkyne partial hydrogenation" else dihydroxylation_rule if mechanism == "Alkene dihydroxylation" else epoxidation_rule if mechanism == "Epoxidation" else chlorination_rule if mechanism == "Chlorination" else bromination_rule if mechanism == "Bromination" else hydrohalogenation_rule if mechanism == "Hydrohalogenation" else hydration_rule if mechanism == "Hydration" else e1_rule if mechanism == "E1" else sn1_rule if mechanism == "SN1" else e2_rule if mechanism == "E2" else sn2_rule if mechanism == "SN2" else alcohol_oxidation_rule if mechanism == "Alcohol oxidation" else carbonyl_hydrogenation_rule if mechanism == "Carbonyl hydrogenation" else hydrogenation_rule
            contract_reagent = [item["mol"] for item in inputs[1:]] if mechanism in {"Alkyne hydrogenation", "Alkyne halogenation", "Alkyne hydrohalogenation"} else inputs[1]["mol"] if len(inputs) > 1 else None
            compatibility_data = reaction_compatibility.mapped_report(compatibility, inputs[0]["mol"], compatibility_rule.edit_contract(inputs[0]["mol"], contract_reagent, site),
                                  **({"charge_changes": alcohol_oxidation_rule.charge_contract(inputs[1]["mol"]),
                                      "consumed_tetrahedral_centers": alcohol_oxidation_rule.consumed_centers(inputs[0]["mol"], site)} if mechanism == "Alcohol oxidation" else
                                     {"charge_changes": sn2_rule.charge_contract(inputs[0]["mol"], inputs[1]["mol"], site),
                                      "inverted_substitutions": [sn2_rule.substitution(inputs[0]["mol"], inputs[1]["mol"], site)]} if mechanism == "SN2" else
                                     {"charge_changes": e2_rule.charge_contract(inputs[0]["mol"], inputs[1]["mol"], site),
                                      "eliminations": [e2_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)]} if mechanism == "E2" else
                                     {"solvolyses": [sn1_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)]} if mechanism == "SN1" else
                                     {"e1_eliminations": [e1_rule.participants(inputs[0]["mol"], site)]} if mechanism == "E1" else
                                     {"consumed_double_bonds": [hydration_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Hydration" else
                                     {"consumed_double_bonds": [hydrohalogenation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Hydrohalogenation" else
                                     {"consumed_double_bonds": [bromination_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Bromination" else
                                     {"consumed_double_bonds": [chlorination_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Chlorination" else
                                     {"consumed_double_bonds": [epoxidation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Epoxidation" else
                                     {"consumed_double_bonds": [dihydroxylation_rule.participants(inputs[0]["mol"], inputs[1]["mol"], site)["alkene"]]} if mechanism == "Alkene dihydroxylation" else {})) if compatibility else None
            elimination_geometry = e2_rule.geometry(inputs[0]["mol"], inputs[1]["mol"], site) if mechanism == "E2" else None
            candidates.append({"name": mechanism, "family": family, "mechanism": mechanism,
                               "reactants": (substrate_id, reagent_id), "equationReactants": tuple(equation_ids),
                               "productName": name, "productSmiles": smiles,
                               "byproducts": [{k: v for k, v in out.items() if k != "mappedSmiles"} for out in outputs[1:]],
                               "mappedProducts": [out["mappedSmiles"] for out in outputs],
                               "site": {"type": mechanism, "atomMaps": site_maps, "substrateAtoms": graph_site, "parameters": parameters,
                                        "label": "Site: " + ", ".join(str(i) for i in site_maps) +
                                                 (" · halogen → carbon " + str(parameters["halogenCarbon"]) if mechanism == "Alkyne hydrohalogenation" else "")},
                               "profile": profile, "explanation": description,
                               "conditions": requirements + ". Conditions are illustrative, not a guarantee. " + extra +
                                             (" Acid catalyst; this pathway is reversible." if mechanism in {"Hydration", "Esterification", "Ester hydrolysis"} else "") +
                                             (" Metal catalyst required." if profile.get("catalyst") == "metal" else ""),
                               "sourceUrl": source,
                               **({"aldehydeOxidationModel": aldehyde_oxidation_conditions.metadata(substrate)} if mechanism == "Aldehyde oxidation" else {}),
                               **({"dehydrationModel": alcohol_dehydration_rule.metadata(inputs[0]["mol"], fragments[0], site, compatibility)} if mechanism == "Alcohol dehydration" else {}),
                               **({"alcoholSubstitutionModel": alcohol_substitution_rule.metadata(inputs[0]["mol"], inputs[1]["mol"], fragments[0], site, compatibility)} if mechanism == "Alcohol substitution" else {}),
                               **({"primaryOxidationModel": primary_alcohol_oxidation_rule.metadata(inputs[0]["mol"], inputs[1]["mol"], fragments[0], site, compatibility)} if mechanism == "Alcohol oxidation" and primary_alcohol_oxidation_rule.is_primary(inputs[0]["mol"], site) else {}),
                               **({"secondaryOxidationModel": secondary_alcohol_oxidation_rule.metadata(inputs[0]["mol"], inputs[1]["mol"], fragments[0], site, compatibility)} if mechanism == "Alcohol oxidation" and secondary_alcohol_oxidation_rule.is_secondary(inputs[0]["mol"],site) else {}),
                               **({"compatibility": compatibility_data} if compatibility_data else {}),
                               **({"hydrogenationSubstrateIdentity": _identity(inputs[0]["mol"]),
                                   "hydrogenationReagentIdentity": _identity(inputs[1]["mol"])} if mechanism == "Hydrogenation" else {}),
                               **({"regioselectivity": {"basis": compatibility["orientationBasis"],
                                                       "alternativeOrientations": compatibility["orientationCount"],
                                                       "oxygenCarbonMap": parameters["oxygenCarbon"],
                                                       "ratios": None, "rearrangements": "not modeled"}} if mechanism == "Hydration" else {}),
                               **({"regioselectivity": {"basis": compatibility["orientationBasis"], "alternativeOrientations": compatibility["orientationCount"],
                                                       "halogenCarbonMap": parameters["halogenCarbon"], "ratios": None, "rearrangements": "not modeled"},
                                   "hxModel": {"mode": "ionic", "hydrogenHalide": compatibility["hydrogenHalide"], "consumedReagent": True,
                                               "radicalPathway": "unsupported", "oxygenSpectators": any(g["type"] in {"alcohol", "ether"} and g["disposition"] == "preserved" for g in compatibility["groups"])}} if mechanism == "Hydrohalogenation" else {}),
                               **({"epoxidationStereo": epoxidation_rule.stereo_metadata(inputs[0]["mol"], fragments[0], inputs[1]["mol"], site)} if mechanism == "Epoxidation" else {}),
                               # Exact validated reagent graph for condition-profile evidence;
                               # never infer a peracid identity from its name or formula.
                               **({"peroxyacidIdentity": _identity(inputs[1]["mol"]),
                                   "epoxidationSubstrateIdentity": _identity(inputs[0]["mol"])} if mechanism == "Epoxidation" else {}),
                               **({"dihydroxylationStereo": dihydroxylation_rule.stereo_metadata(inputs[0]["mol"], fragments[0], inputs[1]["mol"], site),
                                   "dihydroxylationSubstrateIdentity": _identity(inputs[0]["mol"]),
                                   "dihydroxylationReagentIdentity": _identity(inputs[1]["mol"])} if mechanism == "Alkene dihydroxylation" else {}),
                               **({"chlorinationStereo": chlorination_rule.stereo_metadata(inputs[0]["mol"], fragments[0], inputs[1]["mol"], site)} if mechanism == "Chlorination" else {}),
                               **({"brominationStereo": bromination_rule.stereo_metadata(inputs[0]["mol"], fragments[0], inputs[1]["mol"], site)} if mechanism == "Bromination" else {}),
                               **({"alkynePartialStereo": alkyne_partial_hydrogenation_rule.stereo_metadata(inputs[0]["mol"], fragments[0], inputs[1]["mol"], site)} if mechanism == "Alkyne partial hydrogenation" else {}),
                               **({"alkyneCompleteModel": alkyne_complete_hydrogenation_rule.metadata(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site, compatibility)} if mechanism == "Alkyne hydrogenation" else {}),
                               **({"alkyneHalogenModel": alkyne_halogenation_rule.metadata(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site, compatibility,
                                                                                         anti_model=inputs[0].get("alkyneHalogenAntiModel", False))} if mechanism == "Alkyne halogenation" else {}),
                               **({"alkyneHxModel": alkyne_hydrohalogenation_rule.metadata(inputs[0]["mol"], [item["mol"] for item in inputs[1:]], site, compatibility),
                                   "regioselectivity": {"basis": compatibility["orientationBasis"], "alternativeOrientations": compatibility["orientationCount"],
                                                        "halogenCarbonMap": parameters["halogenCarbon"], "ratios": None, "rearrangements": "not modeled"}} if mechanism == "Alkyne hydrohalogenation" else {}),
                               **({"carbocationModel": {"basis": sn1_rule.classification(substrate, site), "rearrangements": "not modeled",
                                                        "resonanceDepiction": "one localized formal contributor" if "resonance" in sn1_rule.classification(substrate, site) else "screened alkyl cation",
                                                        "reactingAtomMap": site_maps[0], "productConfiguration": "unassigned", "racemizationRatio": None}} if mechanism == "SN1" else {}),
                               **({"carbocationModel": {"basis": e1_rule.classification(substrate, site[:2]), "rearrangements": "not modeled",
                                                        "resonanceDepiction": "one localized formal contributor" if "resonance" in e1_rule.classification(substrate, site[:2]) else "screened alkyl cation",
                                                        "reactingAtomMap": site_maps[0], "betaAtomMap": site_maps[2], "productConfiguration": "new alkene unassigned", "stereoisomerRatio": None}} if mechanism == "E1" else {}),
                               "stereochemistry": {"reactant": inspect_stereochemistry(inputs[0]["mol"]), "product": inspect_stereochemistry(fragments[0]),
                                                   "effect": "validated local opposite-face Br2 alternatives where source geometry determines them; distant physical configurations retained and CIP reassigned; unknown internal geometry remains unsigned; no ratios or conformer-derived products" if mechanism == "Bromination" else "validated local opposite-face Cl2 alternatives from source geometry; distant physical configurations retained and CIP reassigned; unknown internal geometry unsigned; no conformer-derived outcomes or ratios" if mechanism == "Chlorination" else "concerted same-face oxygen transfer retains mapped alkene substituent geometry; new configurations only from validated source relationships; distant physical stereo retained and CIP independently recalculated; no face ratios or conformer-derived predictions" if mechanism == "Epoxidation" else "backside inversion; R/S recomputed, not swapped; unaffected mapped configurations independently checked for retention" if mechanism == "SN2" else
                                                             "specified configurations retained in the validated acyl-cleavage edit; CIP labels recomputed, not assumed unchanged" if mechanism in ester_rules.PATHWAYS else
                                                             "validated retention of distant specified configurations and unselected alkene geometry; selected C=C geometry is consumed; new centers remain unassigned" if mechanism == "Hydrogenation" else
                                                             "selected E/Z is consumed; distant specified configurations and unselected pi geometry are independently retained; CIP recomputed; new centers, syn/anti and conformer stereochemical outcomes remain unassigned" if mechanism == "Hydration" else
                                                             "ionic HX net capture: selected E/Z consumed; unaffected mapped configurations and unselected pi geometry independently retained; CIP recomputed; new centers, syn/anti and conformer stereochemical outcomes unassigned" if mechanism == "Hydrohalogenation" else
                                                             "validated retention of distant specified configurations in the C=O-to-alcohol net edit; CIP labels recomputed; new alcohol centers remain unassigned" if mechanism == "Carbonyl hydrogenation" else
                                                             "validated retention of unaffected mapped configurations; only a specified reactive alcohol center becomes an unassigned planar carbonyl; CIP labels recomputed" if mechanism == "Alcohol oxidation" else
                                                             "reacting-center configuration is lost on planar carbocation formation; product configuration and racemization ratio remain unassigned; unaffected mapped configurations are independently retained and CIP reassigned" if mechanism == "SN1" else
                                                             "alpha configuration is lost at planar carbocation formation; selected beta configuration is consumed only on beta-H loss/C=C formation; distant mapped configurations retained and CIP reassigned; new E/Z and ratios unassigned" if mechanism == "E1" else
                                                             "Lindlar net syn addition; internal cis/Z independently assigned from the mapped graph, terminal E/Z not applicable; distant physical configurations retained and CIP recalculated; no catalyst surface mechanism or conformer-derived selectivity" if mechanism == "Alkyne partial hydrogenation" else
                                                             "selected C≡C becomes saturated CH2/CH3 without E/Z or new local centers; distant physical configurations retained and CIP recalculated; surface exchange, facial outcomes and selective multi-site reduction are not predicted" if mechanism == "Alkyne hydrogenation" else
                                                             "first-stage Br/Br anti relationship independently CIP-checked; Cl2 first-stage geometry unsigned; two-equivalent endpoint saturated with no local stereo; distant physical configurations retained; no ratios or conformer-derived assignments" if mechanism == "Alkyne halogenation" else
                                                             "internal first-stage E/Z unassigned; terminal CH2 E/Z not applicable; full geminal endpoint has no local E/Z or new centers; distant physical configurations retained and CIP recomputed; no anti/syn, face ratios or conformer-derived outcomes" if mechanism == "Alkyne hydrohalogenation" else "connectivity only",
                                                   **({"effect": "validated distant retention; only reacting alpha/beta configurations become planar. E/Z is determined only by two specified local tetrahedra with one beta H, otherwise unassigned.",
                                                       "geometry": elimination_geometry} if mechanism == "E2" else {}),
                                                   "geometryRequirement": ("anti-periplanar H–Cβ–Cα–X. " + elimination_geometry["status"] + "; sampled non-anti geometry is not proof of impossibility. Kinematic acyclic rotation, not energy/clash/transition-state validation.") if mechanism == "E2" else None}})
            if mechanism == "Alcohol dehydration":
                candidates[-1]["stereochemistry"]["effect"] = "Only participating alpha/beta carbons become planar; distant physical configurations are checked and CIP independently recalculated. New E/Z stays unassigned; no conformer-derived outcome or product ratio."
            if mechanism == "Alcohol substitution":
                candidates[-1]["stereochemistry"]["effect"] = "Distant physical configurations retained and CIP recalculated. Local HX product configuration unresolved, not retained/flipped by its R/S letter. No secondary universal SN2 inversion or exact SN1 racemization ratio is claimed."
            if mechanism == "Bromination":
                seen_bromination_products.append(candidates[-1])
            if mechanism == "Chlorination":
                seen_chlorination_products.append(candidates[-1])
            if mechanism == "Epoxidation":
                seen_epoxidation_products.append(candidates[-1])
            if mechanism == "Alkene dihydroxylation":
                seen_dihydroxylation_products.append(candidates[-1])
            if mechanism == "Hydrohalogenation":
                seen_hydrohalogenation_products.append(candidates[-1])
    counts = Counter((r["mechanism"], r["reactants"]) for r in candidates)
    indices = Counter()
    result = {}
    for r in candidates:
        if r["mechanism"] == "Alkene dihydroxylation":
            r["stereochemistry"]["effect"] = "Validated syn OH addition from mapped source geometry; distant physical configurations retained and CIP independently recalculated. Unknown internal geometry stays unsigned; no conformer-based assignment or ratios."
            r["site"]["label"] += " · " + r["dihydroxylationStereo"]["outcome"]
            if r["dihydroxylationStereo"]["assignedAtomMaps"]:
                r["site"]["label"] += " · " + ", ".join(f"C{c['atomMap']} {c['assignment']}" for c in r["stereochemistry"]["product"]["chiralCenters"] if c["atomMap"] in r["dihydroxylationStereo"]["assignedAtomMaps"])
        if r["mechanism"] == "Bromination":
            grouped = len(r["site"]["parameters"]["equivalentSiteFaces"])
            r["site"]["label"] += (" · " + r["brominationStereo"]["outcome"] +
                                  (" · " + str(grouped) + " equivalent site/face representations" if grouped > 1 else ""))
            if r["brominationStereo"]["assignedAtomMaps"]:
                r["site"]["label"] += " " + str(r["site"]["parameters"]["faceAlternative"] + 1)
                r["site"]["label"] += " · " + ", ".join(
                    f"C{c['atomMap']} {c['assignment']}" for c in r["stereochemistry"]["product"]["chiralCenters"]
                    if c["atomMap"] in r["brominationStereo"]["assignedAtomMaps"])
        if r["mechanism"] == "Chlorination":
            grouped = len(r["site"]["parameters"]["equivalentSiteFaces"])
            r["site"]["label"] += (" · " + r["chlorinationStereo"]["outcome"] +
                                  (" · " + str(grouped) + " equivalent site/face representations" if grouped > 1 else ""))
            if r["chlorinationStereo"]["assignedAtomMaps"]:
                r["site"]["label"] += " " + str(r["site"]["parameters"]["faceAlternative"] + 1)
                r["site"]["label"] += " · " + ", ".join(
                    f"C{c['atomMap']} {c['assignment']}" for c in r["stereochemistry"]["product"]["chiralCenters"]
                    if c["atomMap"] in r["chlorinationStereo"]["assignedAtomMaps"])
        if r["mechanism"] == "Epoxidation":
            grouped = len(r["site"]["parameters"]["equivalentSiteFaces"])
            r["site"]["label"] += (" · " + r["epoxidationStereo"]["outcome"] +
                                  (" · " + str(grouped) + " equivalent site/face representations" if grouped > 1 else ""))
            if r["epoxidationStereo"]["assignedAtomMaps"]:
                r["site"]["label"] += " " + str(r["site"]["parameters"]["faceAlternative"] + 1)
                r["site"]["label"] += " · " + ", ".join(
                    f"C{c['atomMap']} {c['assignment']}" for c in r["stereochemistry"]["product"]["chiralCenters"]
                    if c["atomMap"] in r["epoxidationStereo"]["assignedAtomMaps"])
        if r["mechanism"] == "Hydrohalogenation":
            equivalents = len(r["site"]["parameters"]["equivalentSiteAtomMaps"])
            if equivalents > 1:
                r["site"]["label"] += f" · {equivalents} graph-equivalent positions"
        key = (r["mechanism"], r["reactants"]); indices[key] += 1
        identifier = PREFIX.get(r["mechanism"], r["mechanism"].lower()) + "-" + r["reactants"][0]
        if "equivalents" in r["site"]["parameters"]:
            identifier += "-" + str(r["site"]["parameters"]["equivalents"]) + "eq"
        if "monomerUnits" in r["site"]["parameters"]:
            identifier += "-" + str(r["site"]["parameters"]["monomerUnits"]) + "units"
        if r["mechanism"] == "Esterification": identifier += "-" + r["reactants"][1]
        if counts[key] > 1: identifier += "-site" + str(indices[key])
        r["site"]["siteId"] = identifier
        result[identifier] = r
    return result, list(dict.fromkeys(notes))
