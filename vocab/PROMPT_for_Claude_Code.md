# Prompt for Claude Code: generate Pash voice clips with ElevenLabs

Copy everything below the line into Claude Code, opened in the folder
`C:\Users\ahmma\Downloads\Virtual Pet Sounds` (the folder that has `pash_voice_lines.csv`).

---

Generate Persian (Farsi) voice clips for my kids' app with the ElevenLabs text-to-speech API.

**Input:** `pash_voice_lines.csv` in this folder (UTF-8 with BOM). Columns: `file_name`, `farsi_text`, `english`, `group`. 892 rows. Generate one clip per row from `farsi_text` and save it as `file_name`.

**Output:** a new subfolder `v2\` in this folder. Every file name must exactly match the `file_name` column (e.g. `where_cat.mp3`).

**API key:** read it from the environment variable `ELEVENLABS_API_KEY`. If it isn't set, ask me to set it in this terminal. Never print the key, write it into any file, or commit it anywhere.

**Settings:**
- Voice ID: `<PASTE VOICE ID HERE>`
- Model: `<PASTE MODEL ID HERE>`, the same one I used on the ElevenLabs website for the earlier Pash clips. If unsure, check the model list endpoint and confirm with me which supports Persian.
- Output format: MP3, 44.1 kHz, 128 kbps (`mp3_44100_128`).
- Use the same voice settings for every clip (stability, similarity, style) so they all sound like one character. Use ElevenLabs' defaults for this voice unless I say otherwise.
- No sound effects, no voice changer, no post-processing filters. Clean voice only.

**How to run it:**
1. Write a small, resumable script (Python or PowerShell, whichever is available on this Windows machine). It skips files that already exist in `v2\`, so re-running continues where it stopped.
2. First generate only these 5 rows as a test: `w_cat.mp3`, `where_cat.mp3`, `this_cat.mp3`, `say_cat.mp3`, `hi.mp3`. Then stop and let me listen before doing the rest.
3. After I approve, generate all rows. Respect API rate limits: run at most 2-3 requests at a time, wait and retry on HTTP 429, and retry other failures up to 3 times.
4. Check every saved file is a valid MP3 larger than 2 KB. List any failures and retry them.
5. Character usage is about 8,200 characters in total. Show me my remaining character quota before the full run, and stop if it isn't enough.

**Important for audio quality:**
- Each clip should end naturally. Don't cut or trim anything; I trim and pad the files myself later.
- If a clip comes back noticeably cut off or garbled, regenerate that one.

**When done:** print a summary: how many files were created, any failures, and total characters used. Don't change or delete any other files in this folder.
