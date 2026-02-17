# GURNEY

Gurney is a web-browsing agent that uses an OpenAI-compatible LLM
to interact with websites based on a natural-language prompt.

Uses Playwright's accessibility snapshot and
semantic locators (get_by_role, get_by_text, etc.) for interactions.

Usage:
    python gurney.py --prompt "Find the price of the first product" \
                    --url "https://example.com" \
                    --endpoint "http://localhost:11434/v1" \
                    --model "llama3" \
                    [--api-key "sk-..."] \
                    [--max-steps 20] \
                    [--headless]