import { mkdir, readFile, writeFile, access } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const images = JSON.parse(await readFile('src/images.json', 'utf8'));
await mkdir('public/media', { recursive: true });
for (const [filename, id] of Object.entries(images)) {
  const path = 'public/media/' + filename;
  if (await access(path).then(() => true, () => false)) continue;
  const url = 'https://assets.super.so/5a468d72-dc70-4542-bbd5-f06872521400/images/' + id + '/' + encodeURIComponent(filename);
  for (let attempt = 1; ; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(45000) });
      if (!response.ok || !response.headers.get('content-type')?.startsWith('image/')) throw new Error('Invalid image response: ' + response.status);
      await writeFile(path, Buffer.from(await response.arrayBuffer()));
      break;
    } catch (error) {
      if (attempt === 3) throw new Error('Unable to import ' + filename, { cause: error });
      await delay(attempt * 1000);
    }
  }
}
