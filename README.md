# AI Swarm · AI Village Explorer

A static, private-data research explorer for [AI Digest's AI Village dataset](https://huggingface.co/datasets/aidigestorg/ai-village).

The public page contains only interface code. Select a prepared folder to explore its contents locally in your browser. Dataset records, tokens, and screenshots are never uploaded by this page. No analytics or third-party JavaScript is loaded.

## Cluster layout

- Code: `~/Work/AI_Swarm/`
- Downloaded source: `~/scratch/AI_Swarm/ai-village/raw/`
- Browser-readable records: `~/scratch/AI_Swarm/ai-village/explorer-data/`

The dataset requires approved Hugging Face access. The standard-library helper runs on Python 3 without package installation:

```bash
python3 ~/Work/AI_Swarm/scripts/dataset.py login
python3 ~/Work/AI_Swarm/scripts/dataset.py download
python3 ~/Work/AI_Swarm/scripts/dataset.py prepare
```

The login prompt hides the token and verifies access before saving it to Hugging Face's conventional token path with owner-only permissions. Never put a token in Git, chat, or a command argument.

The default download includes all non-archive files, including the JSONL tables, transcript, schema, changelog and screenshot index. Add `--with-images` to download all daily screenshot archives as well. The dataset card lists approximately 177 GB including screenshots; allow additional space for prepared records. A snapshot revision is recorded and downloaded files are checked against advertised sizes. Interrupted files are restarted on the next run.

For long preparation jobs, use the cluster scheduler in accordance with your allocation. Preparation uses bounded batches (500 rows or approximately 2 MB of source text). A single unusually large record can exceed that size. Use a fresh `--output` directory for each later snapshot.

## Recommended: keep data on the cluster

Start the read-only server on the cluster after preparation:

```bash
python3 ~/Work/AI_Swarm/scripts/serve.py
```

On your computer, open an SSH tunnel and leave its terminal running:

```bash
ssh -N -L 8866:127.0.0.1:8866 YOUR_CLUSTER_SSH_ALIAS
```

Open the GitHub Pages site and choose **Connect to cluster**. The server binds only to cluster loopback, not a public interface. Browser requests go to `http://localhost:8866` through your authenticated SSH tunnel. It serves only the prepared dataset and selected screenshots, never arbitrary home-directory files. Only the expected GitHub Pages origin and local development origin receive CORS permission. Your browser may require permission for local-network access; if the browser blocks this connection, use local-folder mode below. The tunnel and server must stay running while browsing.

## Optional: local-folder mode

Copy the prepared folder to your computer:

```bash
scp -r YOUR_CLUSTER_SSH_ALIAS:~/scratch/AI_Swarm/ai-village/explorer-data ./explorer-data
```

Alternatively, open the GitHub Pages site and choose **Open data folder**. Select `explorer-data`, not its parent. A desktop browser with directory selection and Web Workers is required. Screenshots can be read separately from a downloaded daily `.tar` archive using the record dialog; images are not included in the prepared folder.

## Exploration

- Every source `.jsonl.gz` table is prepared with every original field intact.
- Table-wide charts show daily record counts and agent counts (computer turns are joined through their session).
- Search scans all chunks in the selected table, in a worker, with exact matching totals and 50 records per page. Filters combine text, agent, UTC date range, and action/role.
- Search a session or agent ID across related tables to trace records. This is a raw-record explorer, not an inferred social-network or causal analysis.
- Screenshot lookup uses the turn ID and the archive's PNG member. Redacted screenshots are labeled.
- Timeline and agent charts describe the whole selected table; record filters apply to the result list. Records retain source file order.

## Interpretation and limits

Counts represent records, not unique actions across tables, success, or model quality. Tables overlap. Generated summaries and agent narratives are unverified claims. Read the source SCHEMA.md and CHANGELOG.md before interpreting behavior changes. The preparer follows the source schema, including event speakerId/agentId, chat agent_speaker_id, and computer-turn session-to-agent joins. Timeline charts use record creation dates, which can differ from dates described by a summary or goal.

The transcript is a convenient duplicate presentation of events rather than a separate visualized table. Source documentation and screenshot archives remain in raw storage. Searching a large computer-use table can take time because all candidate chunks are scanned after date/agent/type pruning; prepared copies also use gzip compression but consume additional storage. Browser memory remains bounded to batches and the current page, except the compact manifest and file references.

The public source repo must never contain restricted records. GitHub Pages deploys only four interface files. Research terms remain those of the source dataset; cite AI Digest / AI Village, 2026.

## Development

Serve the directory with `python3 -m http.server 8765`. No frontend dependencies or build step. The optional read-only WebMCP dataset-status tool is feature-detected; its supported-browser integration has not been verified.
