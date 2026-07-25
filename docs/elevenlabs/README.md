# ElevenLabs docs (offline snapshot)

Pulled 2026-07-25 from [elevenlabs.io/docs](https://elevenlabs.io/docs). Use this folder as the local reference for Kissa **Voice / performance audio** (PRD §6.5).

Live index: https://elevenlabs.io/docs/llms.txt  
OpenAPI: `openapi.json` (also https://elevenlabs.io/openapi.json)

## Auth

- Header: `xi-api-key: <key>`
- Env: `ELEVENLABS_API_KEY`
- Create key: https://elevenlabs.io/app/settings/api-keys
- **Never call ElevenLabs from the Vite browser** — key stays in `api` / `worker` only.

## SDKs

```bash
# Python (backend worker)
pip install elevenlabs

# TypeScript (only if a Node worker needs it — prefer Python for Kissa)
npm install @elevenlabs/elevenlabs-js
```

## Endpoints we care about

| Use | Method | Path |
|-----|--------|------|
| Batch TTS (default for Kissa stems) | `POST` | `/v1/text-to-speech/{voice_id}` |
| TTS + char timestamps (beat clock) | `POST` | `/v1/text-to-speech/{voice_id}/with-timestamps` |
| Stream TTS | `POST` | `/v1/text-to-speech/{voice_id}/stream` |
| Stream + timestamps | `POST` | `/v1/text-to-speech/{voice_id}/stream/with-timestamps` |
| Multi-speaker dialogue (v3) | `POST` | Text to Dialogue API |
| List / search library voices | | Voices + Voice Library APIs |
| SFX (optional later) | | Sound effects API |
| Forced alignment | | Forced Alignment API |

Base: `https://api.elevenlabs.io` (also US / EU / IN / SG residency hosts).

## Models (pick for Kissa)

| Model ID | When | Languages | Max chars/req |
|----------|------|-----------|---------------|
| `eleven_multilingual_v2` | **Default narration** — stable long-form, Hindi+English | 29 incl. `hi`, `en` | 10k |
| `eleven_v3` | Max emotion / audio tags / dialogue | 70+ incl. Hindi | 5k |
| `eleven_flash_v2_5` | Fast/cheap drafts, not wow-demo mix | 32 incl. `hi` | 40k |

PRD demo = **wow audio** → prefer `eleven_multilingual_v2` or `eleven_v3`, not Flash.

Request stitching (`previous_request_ids` / `previous_text`) works on multilingual v2 — **not** on `eleven_v3`.

## Minimal convert call (Python)

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",  # library voice
    text="Meera clutched the ticket until the edges went soft.",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)
# write bytes to /data/... stem file
```

## Body knobs that map to NarrationPlan

- `text` ← `seq` narration_turn / dialogue_beat text (+ optional v3 `[emotion]` audio tags)
- `voice_id` ← cast from `voice_library` (PRD: library only, no cloning v1)
- `model_id` ← series language/quality policy
- `voice_settings`: `stability`, `similarity_boost`, `style`, `use_speaker_boost`, `speed`
- `seed` ← more consistent regenerations (still not fully deterministic)
- `previous_text` / `next_text` / `previous_request_ids` ← stitch turns in a part
- `pronunciation_dictionary_locators` ← name / dialect glossary
- Timestamps endpoint ← align stems to beat clock (or use WhisperX later)

Output default: `mp3_44100_128`. PCM/WAV 44.1k needs higher plan tiers.

## Files in this folder

| File | What |
|------|------|
| `llms.txt` | Full docs index |
| `openapi.json` | Full OpenAPI 3.1 |
| `text-to-speech.mdx` | TTS capability overview |
| `models.mdx` | Model matrix |
| `voices.mdx` | Voice library / cloning / design |
| `best-practices.md` | Prompting, pauses, v3 audio tags |
| `convert.md` | Create speech API |
| `convert-with-timestamps.md` | Timing for beat clock |
| `stream.mdx` / `stream-with-timestamps.mdx` | Streaming variants |
| `streaming-guide.md` | How-to stream |
| `request-stitching.md` | Prosody across chunks |
| `text-to-dialogue.md` | Multi-speaker v3 dialogue |
| `forced-alignment.md` | Audio↔text alignment |
| `sound-effects.md` | Gen SFX (companion to library beds) |
| `quickstart.mdx` | First API call |
| `authentication.md` | API keys |
| `tts-cookbook.md` | Cookbook entry |
| `api-tts-llms.txt` | TTS API section index |
| `eleven-api-llms.txt` | ElevenAPI guides index |

## Kissa wiring notes

1. Worker job: for each `NarrationPlan` `seq_id`, call convert → write stem under `/data`.
2. Regen-by-`seq_id` = one TTS request, not whole part.
3. Cast Hindi + English library voices; do **not** ship cloning in v1.
4. Emotion: map script `emotion` → v3 `[tags]` and/or `voice_settings`; regenerate weak lines.
5. Concurrency: bound parallel TTS under plan limits (Free≈4 Flash; Multilingual ≈ half).
6. Cache by hash of (text, voice_id, model, settings, seed) to avoid double-billing.
