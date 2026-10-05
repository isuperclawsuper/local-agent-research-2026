from pathlib import Path
root=Path('/var/minis/shared/local-agent-research-2026/folo-2026')
for d in ['jev-input','jev-output']:(root/d).mkdir(exist_ok=True)
source=Path('/var/minis/workspace/local-agent-research/score.py').read_text()
source=source.replace("ROOT=Path('/var/minis/shared/local-agent-research-2026')","ROOT=Path('/var/minis/shared/local-agent-research-2026/folo-2026')")
source=source.replace('max_workers=4','max_workers=6')
exec(compile(source,'folo-annual-score','exec'))
