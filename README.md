# GURNEY

Gurney is a web-browsing agent that uses an OpenAI-compatible LLM
to interact with websites based on a natural-language prompt.

Uses Playwright's accessibility snapshot and
semantic locators (get_by_role, get_by_text, etc.) for interactions.

## Setup

```bash
pip3 install -r requirements.txt
playwright install chromium
```

Set your API key in `.env`:
```
GEMINI_API_KEY=your-key-here
```

## Usage

```bash
python3 gurney.py --prompt "Log in this website"
```

By default it navigates to **https://learnpf.ai** using **Gemini 2.0 Flash**.

### All options

| Flag | Default | Description |
|---|---|---|
| `--prompt` | *(required)* | Goal / task for the agent |
| `--no-headless` | off | Run browser with a window |

### Actions

The agent has two interaction primitives:

- **click** — target by `role`/`name`, or by visible `text`
- **fill** — target by `role`/`name`, `label`, or `placeholder`

Plus **answer** to return a final result. 3-second delay between every interaction.

### Screenshots

A full-page screenshot is automatically saved to `screenshots/` before the browser exits. Useful for debugging what the agent last saw.
