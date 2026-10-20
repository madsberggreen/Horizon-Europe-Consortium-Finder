---
description: Open the start form — find Horizon Europe calls, partners and pitch letters for a researcher with one click
---

# /start

Shows the start form inside the chat. The user fills it in and presses **Find me a consortium!**; the form then sends the request as the user's next message and the pipeline runs.

## Show the form

1. If you have the `show_widget` tool (Imagine / visualize), call its `read_me` first if this conversation hasn't yet (modules: `interactive`), then call `show_widget` with:
   - `title`: `consortium_finder_form`
   - `loading_messages`: `["Laying out the form"]`
   - `widget_code`: the full contents of `${CLAUDE_PLUGIN_ROOT}/start/form.html`, **verbatim** — read the file and pass it unchanged. Never rewrite, shorten or restyle it.
   Before the call, write one line: "Fill in the form and press **Find me a consortium!** Simple search uses only publicly available data." Write nothing after the call.
2. If you don't have `show_widget`, ask in plain text for name, institution, optional ORCID iD, and whether they want a simple search (public data only) or an advanced search (their own idea and documents). For advanced search, first show this warning and wait for a yes: "Check your institutional guidelines on AI use before uploading any data. Only upload data that you or your institution has full ownership of." Then ask for the idea and invite them to attach documents in the chat. Also mention the start page https://claude.ai/artifact/R1rkx8dabe6gKRKpYNZ43E as an alternative.

## When the request arrives

The form's message starts with `Find me a consortium!` followed by `Mode:`, `Name:`, `Institution:`, optional `ORCID:`, and in Advanced mode `Research idea:` / `Document:` blocks between `<<<` and `>>>`. Treat it exactly as an `/add-researcher` request in that format and run the full pipeline in `${CLAUDE_PLUGIN_ROOT}/commands/add-researcher.md` (read it if it isn't in context), starting at step 0. Do not ask for confirmation first. Documents the user attached in the chat instead (plain-text fallback) count as `Document:` blocks.
