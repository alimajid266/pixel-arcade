# Pixel Arcade

One static website containing both verified HTML5 Canvas games:

- `/flappy/` — Flappy Canvas
- `/zombie-defense/` — Zombie Defense
- `/` — shared arcade launcher

## Architecture

Each game remains a self-contained HTML document, but navigation uses same-origin paths. The shared origin provides one Vercel project and one public link. No framework, build command, backend, database, or runtime dependency is required.

Audio is generated procedurally with Web Audio after a user gesture. Music and sound effects have independent persistent controls. Flappy and Zombie use distinct `localStorage` key prefixes, preventing collisions on the shared origin.

## Local development

```bash
python3 -m http.server 8770 --bind 127.0.0.1
```

Open <http://127.0.0.1:8770/>.

## Vercel

Import `alimajid266/pixel-arcade` as one static Vercel project. Keep the framework preset as **Other** and leave build/output commands empty. All routes are plain static directories with `index.html` files.

The previous standalone repositories and deployments should remain available until this combined production site is verified. Browser save data from the old domains cannot automatically transfer to the new origin.
