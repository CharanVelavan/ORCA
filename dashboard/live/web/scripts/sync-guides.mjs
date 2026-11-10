/** Copy the actual repository guides into the offline dashboard before serving or building. */
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../../..');
const destination = resolve(here, '../public/docs');
const guides = [
  ['guide.md', 'guide.md'],
  ['docs/JUDGE_REPRODUCIBILITY.md', 'JUDGE_REPRODUCIBILITY.md'],
  ['docs/JUDGE_WINDOWS.md', 'JUDGE_WINDOWS.md'],
];
try {
  // Read all sources before writing any, so a missing source cannot leave a partly refreshed set.
  const files = await Promise.all(guides.map(async ([source, name]) => ({ name, content: await readFile(resolve(root, source)) })));
  await mkdir(destination, { recursive: true });
  await Promise.all(files.map(({ name, content }) => writeFile(resolve(destination, name), content)));
  process.stdout.write(`Synced ${files.length} local guides to public/docs.\n`);
} catch (error) {
  process.stderr.write(`Guide sync failed: ${error instanceof Error ? error.message : String(error)}\nRestore guide.md, docs/JUDGE_REPRODUCIBILITY.md and docs/JUDGE_WINDOWS.md in the repository, then retry.\n`);
  process.exitCode = 1;
}
