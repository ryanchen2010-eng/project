/** Expand the reviewed COD 1534198 asymmetric sites into one unique C 2/m cell.
 * This is intentionally not a general CIF parser or symmetry engine. */
export function rhodiumUnitCell(cif: string): string {
  const expected = ['_cell_length_a 5.95', '_cell_length_b 10.3', '_cell_length_c 6.03',
    '_cell_angle_alpha 90', '_cell_angle_beta 109.2', '_cell_angle_gamma 90',
    'Cl1 Cl-1 0.226 0 0.219 1 0.0', 'Cl2 Cl-1 0.25 0.175 -0.219 1 0.0', 'Rh1 Rh+3 0 0.167 0 1 0.0'];
  if (!expected.every(line => cif.split(/\r?\n/).includes(line))) throw new Error('Crystal reference differs from the reviewed unit cell.');
  const sites: [string, number, number, number][] = [['Cl', 0.226, 0, 0.219], ['Cl', 0.25, 0.175, -0.219], ['Rh', 0, 0.167, 0]];
  const wrap = (n: number) => ((n % 1) + 1) % 1;
  const unique = new Map<string, [string, number, number, number]>();
  for (const [element, x, y, z] of sites) {
    for (const [a, b, c] of [[x,y,z],[-x,y,-z],[-x,-y,-z],[x,-y,z], [x+.5,y+.5,z],[-x+.5,y+.5,-z],[-x+.5,-y+.5,-z],[x+.5,-y+.5,z]]) {
      const xyz = [wrap(a), wrap(b), wrap(c)].map(v => Math.round(v * 1000000) / 1000000);
      unique.set(`${element}:${xyz.join(',')}`, [element, xyz[0], xyz[1], xyz[2]]);
    }
  }
  const atoms = [...unique.values()];
  if (atoms.length !== 16 || atoms.filter(a => a[0] === 'Rh').length !== 4) throw new Error('Crystal symmetry expansion failed.');
  const header = cif.slice(0, cif.indexOf('loop_'));
  return `${header}loop_\n_atom_site_label\n_atom_site_type_symbol\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\n${atoms.map(([el,x,y,z], i) => `${el}${i+1} ${el} ${x} ${y} ${z}`).join('\n')}\n`;
}
