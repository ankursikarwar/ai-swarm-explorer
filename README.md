# AI Swarm · AI Village Explorer

A self-contained GitHub Pages visualization of [AI Digest's AI Village dataset](https://huggingface.co/datasets/aidigestorg/ai-village).

The site loads `data/summary.json` directly from GitHub Pages. No SSH, local server, login, file upload, or runtime cluster access is required. Public data consists of aggregate counts by date, AI agent, category, and source table, plus AI-agent names/models and source-field coverage. A separate `data/reviewed-records.json` contains 31 manually reviewed content fields or excerpts from eight tables. Original record IDs, timestamps, and excerpt/redaction labels are shown. The rest of the source records, raw model outputs, human identities, and screenshots are not bundled.

## Features

- Every JSONL table is included in the aggregate statistics; totals are checked when the page loads.
- A Reviewed records section opens the actual published text or action fields. It is a small, non-representative selection, not all 3.65 million source records.
- Record content is rendered as plain text, never executed as HTML or commands.
- Interactive daily, weekly, and monthly timelines.
- Agent rankings, action/category distributions, and a daily breakdown.
- Combined date, agent, category, and label search filters.
- All charts follow the selected filters.
- Source revision, generation date, schema field names, and interpretation guidance.

Counts measure activity, not performance. Tables overlap. Dates use record creation timestamps in UTC. Computer turns are linked to agents through sessions; events and chats use their documented speaker fields. The source's transcript is a duplicate presentation of underlying records, not an additional table.

## Refresh the statistics

The source dataset requires approved Hugging Face access. Scripts use the Python standard library. Run on your own approved data machine:

```bash
python3 scripts/dataset.py login
python3 scripts/dataset.py download
python3 scripts/aggregate.py
```

The helper defaults to `~/scratch/AI_Swarm/ai-village/` for large files. `download --with-images --workers 4` downloads screenshots too, but screenshots are unnecessary for these aggregate charts. Downloaded files are pinned to a repository revision and checked against advertised sizes. Tokens are never included in the website or Git.

Copy the resulting `public-summary.json` into `data/summary.json`, verify its counts, then commit and push. The GitHub Actions workflow publishes only the HTML, styles, JavaScript, and summary data.

## Development

Serve this directory with `python3 -m http.server 8765`. No build step or frontend dependencies. The optional, read-only WebMCP status tool is feature-detected.

Source attribution: AI Digest / AI Village, 2026. Consult the source research terms and CHANGELOG before using the data or interpreting changes in agent behavior.

## Reviewed examples

The explicit source IDs and field/excerpt boundaries are in `scripts/export_reviewed.py`. The public sample was reviewed before publication; it excludes a candidate that contained an email/account identity and other candidates with unreviewed operational details. One local application address was removed and labeled. Do not automatically broaden this allowlist or publish fresh source text during aggregate refreshes. Preserve the reviewed file and its independent snapshot revision until new content has been reviewed.
