"""One concerted textbook peroxyacid transfer, no stable intermediate.

The four arrows are formal electron-pair bookkeeping, not a claim of perfectly
synchronous bond changes, a transition-state geometry or computed electron flow.
"""
from rdkit import Chem
if __package__:
    from . import epoxidation_rule as rule, reaction_compatibility as compatibility
    from .reaction_diagrams import _species, _combine, _finish, _changes
else:
    import epoxidation_rule as rule, reaction_compatibility as compatibility
    from reaction_diagrams import _species, _combine, _finish, _changes


def electron_contract(p):
    a,b = p["alkene"]
    t,h,q,c,o = (p[k] for k in ("transferredOxygen", "peracidHydrogen", "proximalOxygen", "acylCarbon", "carbonylOxygen"))
    return [("pi-attack", (a,b), (a,t), "Alkene pi electrons form the first C–O bond to the terminal peroxyacid oxygen."),
            ("ring-closure", (t,h), (t,b), "The peracid O–H electron pair forms the second C–O bond in the same concerted transfer."),
            ("acid-carbonyl", (q,t), (c,q), "O–O cleavage supplies the new acid C=O bond at the proximal oxygen."),
            ("proton-transfer", (c,o), (o,h), "The original carbonyl pi pair forms O–H as that C=O becomes C–O; the peracid proton stays in the acid coproduct.")]


def validate(initial, after, substrate, reagent, site, moves):
    rule.validate(initial, after, substrate, reagent, site)
    p = rule.participants(substrate,reagent,site)
    actual = [(m["id"], m["source"]["type"], tuple(m["source"]["atomMaps"]),
               m["destination"]["type"], tuple(m["destination"]["atomMaps"])) for m in moves]
    expected = [(name,"bond",source,"bond",destination) for name,source,destination,_ in electron_contract(p)]
    if actual != expected:
        raise ValueError("Epoxidation requires all four exact concerted electron sources/destinations, including the actual acid carbonyl/proton roles.")
    indexed = {a.GetAtomMapNum():a.GetIdx() for a in initial.GetAtoms()}
    after_indexed = {a.GetAtomMapNum():a.GetIdx() for a in after.GetAtoms()}
    for _,source,destination,_ in electron_contract(p):
        before = initial.GetBondBetweenAtoms(*(indexed[m] for m in source))
        after_bond = after.GetBondBetweenAtoms(*(after_indexed[m] for m in destination))
        if before is None or after_bond is None:
            raise ValueError("A concerted electron source or resulting bond is absent.")


def build(reaction, catalog):
    if __package__:
        from .reaction_mechanisms import endpoint, electron_move, molecule_record, validate_step
    else:
        from reaction_mechanisms import endpoint, electron_move, molecule_record, validate_step
    inputs, next_map = [], 1
    for identifier in reaction["equationReactants"]:
        item,next_map = _species(identifier,catalog[identifier],next_map); inputs.append(item)
    substrate,reagent = inputs[0]["mol"],inputs[1]["mol"]
    site = reaction["site"]["substrateAtoms"]
    p = rule.participants(substrate,reagent,site)
    initial = _combine(inputs); editor = Chem.RWMol(initial)
    rule.edit(editor,initial,substrate,reagent,site); after = _finish(editor)
    moves = [electron_move(name,endpoint("bond",*source),endpoint("bond",*destination),description)
             for name,source,destination,description in electron_contract(p)]
    validate_step(initial,after); validate(initial,after,substrate,reagent,site,moves)
    parser=Chem.SmilesParserParams(); parser.removeHs=False
    outputs = [{"mol":Chem.MolFromSmiles(s,parser)} for s in reaction["mappedProducts"]]
    expected = _combine(outputs)
    if (compatibility.mapped_bonds(expected) != compatibility.mapped_bonds(after)
            or Chem.MolToSmiles(expected) != Chem.MolToSmiles(after)):
        raise ValueError("Concerted epoxidation state and both mapped net products disagree.")
    changes = _changes([{"mol":initial}],[{"mol":after}])
    step = {"id":"epoxidation-step-1", "title":"Concerted oxygen transfer", "concerted":True,
            "description":"Both C–O bonds, O–O cleavage, intramolecular proton transfer and acid carbonyl reorganization belong to one formal concerted step. No carbocation, halonium, free hydroxide or stable intervening state is introduced. Face alternatives do not establish facial selectivity.",
            "electronMoves":moves, "beforeState":molecule_record(initial,"Alkene and actual peroxyacid","Starting state"),
            "state":molecule_record(after,"Epoxide and actual carboxylic acid","Product state"), "intermediate":None,
            "protonTransfers":[c for c in changes if "H" in c["atoms"] and c["kind"] in {"formed","broken"}],
            "bondsFormed":[c for c in changes if c["kind"] == "formed"],
            "bondsBroken":[c for c in changes if c["kind"] == "broken"],
            "bondOrderChanges":[c for c in changes if c["kind"] == "order"]}
    return {"version":1, "type":"Epoxidation", "siteId":reaction["site"]["siteId"],
            "roles":{"alkene-carbon-1":p["alkene"][0],"alkene-carbon-2":p["alkene"][1],
                     **{k:v for k,v in p.items() if k != "alkene"}},
            "steps":[step], "solventSpecies":[],
            "energyProfile":{"qualitative":True,"stepCount":1,"rateDeterminingStep":1,"intermediates":0,"activationEnergies":None,
                             "note":"One formal concerted-step topology only. No barrier, synchrony, rate-limiting event or experimental kinetics is calculated."},
            "limitations":["Four-arrow textbook electron-pair bookkeeping; actual electron-flow timing/asynchronicity and transition-state geometry are not computed.",
                           "Stereospecific relative geometry is distinct from facial selectivity; no face ratio or selective one-site conversion is assigned.",
                           "The displayed epoxide/acid state is conditional on the supported net model. Subsequent acid-promoted ring opening or rearrangement is not implemented.",
                           "3D links only the final main product; acid-coproduct atoms remain inspectable in the complete mapped 2D mechanism."]}
