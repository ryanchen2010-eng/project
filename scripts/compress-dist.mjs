// Precompress built assets; this is a build step, not a public web server.
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, extname } from 'node:path';
import { gzipSync } from 'node:zlib';

const outputRoot = resolve('dist');
const compressedTypes = new Set(['.html', '.js', '.css', '.json', '.svg', '.wasm', '.sdf']);

async function compressDirectory(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) {
      await compressDirectory(path);
    } else if (entry.isFile() && compressedTypes.has(extname(path))) {
      const source = await readFile(path);
      if (source.length >= 1024) {
        const compressed = gzipSync(source, { level: 9 });
        if (compressed.length < source.length) await writeFile(`${path}.gz`, compressed);
      }
    }
  }
}

await compressDirectory(outputRoot);
