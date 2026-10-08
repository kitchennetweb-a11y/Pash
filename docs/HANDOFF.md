# Pash handoff (moving from a cloud session to Claude Code)

## What Pash is
A 3D robot virtual pet that teaches a 3-year-old Farsi through play. My son played with it for hours on day one. Live: https://kitchennetweb-a11y.github.io/Pash/

## Repo layout
| Path | What |
|---|---|
| `index.html` | Hosted build that GitHub Pages serves. It's `src_pash-robot.html` wrapped in a doctype/head (see Build), with all audio embedded as base64. |
| `src_pash-robot.html` | Source page, written as an artifact fragment: no `<html>`/`<head>`, starts with `<title>` and `<style>`. Edit this one. |
| `audio/*.mp3` | The 104 processed voice clips currently in use (same as what's embedded). Key = file name. |
| `vocab/words.py`, `vocab/words.json` | The 200 new words: id, Farsi, transliteration, English, emoji picture, category, kind (n = noun, a = action/feeling). |
| `vocab/pash_voice_lines.csv` | All 892 lines to generate with ElevenLabs: existing lines re-recorded clean, plus w_/where_/this_/say_ lines for the new words. |
| `vocab/PROMPT_for_Claude_Code.md` | Prompt for generating the clips with the ElevenLabs API on the PC. |
| `tools/process_robo_clips.py` | Audio pipeline: trim leading silence, compress, level-match, pad the tail. Needs ffmpeg and numpy; paths inside need updating. |
| `tools/test_*_playwright.py` | Headless browser tests used during development. They expect a local copy of three.js; adjust paths. |
| `docs/decisions.md` | Product, voice and tech decisions. Read it first. |

### Build (how index.html is made)
`index.html` = `<!doctype html><html lang="en"><head>` + the meta tags (charset, viewport with viewport-fit=cover, apple-mobile-web-app-capable, apple-mobile-web-app-title "Pash", theme-color) + `</head><body>` + the contents of `src_pash-robot.html` + `</body></html>`.
Audio is currently embedded: `const VOICE_B64={key: base64mp3,...}` in the source. Rebuild it from `audio/` with a small Python script (base64-encode each mp3, keyed by file name).

## How the code is organised (inside src_pash-robot.html)
- **Sound:** `SFX` (synthesised), `music()`, `hush()` (pauses the mic while Pash makes sounds).
- **Voice:** `VOICE_B64`, `VOICE` (decoded buffers), `playVoice(k)` (with the gain boost for Robo keys), `LINES` (key → [Farsi, transliteration (English)]), `VARIANTS` + `pickVar` (random alternative lines), `say(k)` (bubble + voice + stats), `sayAsync(k)`, `fallbackFor(k)` (where_/this_/say_ → word clip if missing).
- **Scene:** three.js r128, robot built from primitives (`rbox`), face drawn on a canvas texture (`drawFace`, faces: happy, laugh, shock, dizzy, sleep, hidden, listen), particles (`emit`).
- **Room:** walls, window, floor and rug textures, lighting; `setLights(on)` switches day/night; `ROOM_DAY` / `ROOM_NIGHT`.
- **Furniture:** `furnGroup`, `tapFurniture` (lamp, bed, chair, table, book).
- **Behaviour:** `st.mode` (idle, dance, sleep, chase, eat, peek, fly, listen, game), `poke(part)`, springs, idle routines.
- **Games:** `WORDS`, `BODY`, `FURN`, `MAKE` (3D toys and food), `playFind`, `playFeed`, `playSay`, `playMoves`, `answer()`, `ask()`, `endGame()`.
- **Talk-back:** `talk` object, `micOn`, `onMic` (voice activity detection), `finishClip`, `playBack` (pitch 1.65).
- **Parent corner:** `stats` in localStorage key `pash-stats-v1`; `statAdd`, `renderParent`; opened by holding the gear for 1.8 s.
- **UI:** `#bar` (text+icon buttons along the bottom; being replaced), `onBtn()`, `#start` overlay, `#micHelp`, `#parent`.

## Status
Done and live: everything listed in decisions.md under Product, apart from the items marked "not built yet".

### In progress / next (requested by the user on 2026-10-08)
1. **Generate voices.** The user runs `vocab/PROMPT_for_Claude_Code.md` with their voice ID and model. Output goes to `C:\Users\ahmma\Downloads\Virtual Pet Sounds\v2\`. Then process every clip (trim leading silence, light compression, level-match, about 0.35 s tail pad, no effects) and replace `audio/`.
2. **Audio restructure.** Stop embedding base64. Load `audio/<key>.mp3` on demand with a manifest (`audio/manifest.json`). Replace sync `VOICE[k]` existence checks with a `HAS(k)` set, and make `sayAsync` await loading. Preload core clips at start, and the next word on the Say it screen.
3. **Icon-only UI.** Round buttons with big emoji, no text, in a left and a right column; phone friendly (about 56 px on phones, 68 px on iPad). Remove the bottom text bar.
4. **Three rooms with bottom navigation:** 🏠 home, 🧸 play, 🛏️ bed, plus 🗣️ for the Say it screen.
   - **Home:** table, chair, book, window, picture, maybe a TV. Buttons: Talk, Feed, Jump, Dance, Moves, Peekaboo.
   - **Play room:** toy shelf, blocks, drum, kite, teddy, brighter wall. Buttons: Ball, Find, Bubbles, Dance, Moves, Talk.
   - **Bedroom:** bed, lamp (day/night), night stand, star mobile, blue walls. Buttons: Sleep, Peekaboo, Talk.
   - Fade transition between rooms. Raycasting must ignore hidden furniture: three r128's raycaster doesn't check visibility, so filter by the visible parent chain.
5. **Say it screen:** a big emoji picture card. Pash says "بگو X!" (`say_X`), waits up to about 8 s listening, then praises any attempt (plays it back squeaky, cheer, a yay variant, then models the word with `w_X`). Next and repeat buttons are icons. Use all 220 words. Record `said` stats. Without a mic, wait about 3.5 s, then model the word.
6. **Find with the new words** (optional): flat emoji cards as items.
7. Re-test (playwright), then publish: commit and push `main`; GitHub Pages updates on its own.

### Known gotchas
- iPad and Safari need one tap before audio or the mic will start (the "Wake up" button does both).
- The mic only works over https on GitHub Pages; it's blocked inside the Claude artifact viewer.
- Clip timings: `sayAsync` waits for the decoded duration plus 250 ms. Padded clips make games slightly slower; that's acceptable.
- Large single HTML files load slowly on iPad, which is another reason to split the audio out.
- Stray `[hidden]` CSS: the page sets `[hidden]{display:none!important}` itself, because the hosted build has no artifact skeleton reset.
