import json,subprocess,concurrent.futures,time
from pathlib import Path
from bs4 import BeautifulSoup
from markdownify import markdownify
ROOT=Path('/var/minis/shared/local-agent-research-2026/folo-2026');ROOT.mkdir(exist_ok=True)
for d in ['pages','raw','articles']: (ROOT/d).mkdir(exist_ok=True)
CLI='/root/.npm/_npx/262514ac33b63ab3/node_modules/folocli/dist/index.js'
def call(args):
 for attempt in range(3):
  r=subprocess.run(['node',CLI]+args,capture_output=True,text=True,timeout=100)
  try:j=json.loads(r.stdout)
  except:continue
  if j.get('ok'):return j['data']
 raise RuntimeError('CLI request failed '+str(j.get('error')))
def feed(f):
 id=f['folo_id'];cursor=None;seen=set();rows=[];boundary=None
 for page in range(150):
  args=['timeline','--feed',id,'--limit','50']
  if cursor:args+=['--cursor',cursor]
  d=call(args);(ROOT/'pages'/f'{id}-{page:03}.json').write_text(json.dumps(d,ensure_ascii=False))
  entries=d.get('entries',[])
  for x in entries:
   e=x['entries'];dt=e.get('publishedAt','');eid=e['id']
   if dt<'2026-01-01':boundary=dt
   if '2026-01-01'<=dt<'2027-01-01' and eid not in seen:
    seen.add(eid);rows.append({'id':eid,'source':f['source'],'feed_id':id,'title':e.get('title'),'url':e.get('url'),'date':dt})
  nc=d.get('nextCursor')
  if boundary or not entries or not d.get('hasNext') or nc==cursor:break
  cursor=nc
 result={'source':f['source'],'feed_id':id,'count':len(rows),'boundary':boundary,'exhausted':not d.get('hasNext'),'pages':page+1,'articles':rows}
 (ROOT/f'catalog-{id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('CATALOG',f['source'],len(rows),'boundary',boundary,flush=True);return result
feeds=json.load(open('/var/minis/shared/local-agent-research-2026/folo-research/feed-map.json'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:cats=list(pool.map(feed,feeds))
(ROOT/'coverage.json').write_text(json.dumps(cats,ensure_ascii=False,indent=2))
rows={x['id']:x for c in cats for x in c['articles']}
def article(a):
 try:
  raw=ROOT/'raw'/f"{a['id']}.json"
  d=json.loads(raw.read_text()) if raw.exists() else call(['entry','get',a['id']])
  raw.write_text(json.dumps(d,ensure_ascii=False));e=d.get('entries',{});html=e.get('content') or ''
  if not html:
   rd=call(['entry','read',a['id']]);(ROOT/'raw'/f"{a['id']}-read.json").write_text(json.dumps(rd,ensure_ascii=False));html=rd.get('content') or rd.get('readability',{}).get('content') or ''
  text=BeautifulSoup(html,'html.parser').get_text('\n',strip=True);a.update(chars=len(text),text=text,fulltext_obtained=bool(html))
  md=f"# {a['title']}\n\n- 来源：{a['source']}\n- 日期：{a['date']}\n- 原文：{a['url']}\n- 存档来源：Folo 历史缓存正文\n\n---\n\n"+markdownify(html,heading_style='ATX')
  (ROOT/'articles'/f"{a['id']}.md").write_text(md);print('TEXT',a['id'],len(text),flush=True)
 except Exception as ex:a.update(error=str(ex),fulltext_obtained=False);print('ERROR',a['id'],str(ex),flush=True)
 return a
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:out=list(pool.map(article,rows.values()))
(ROOT/'all-2026.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('DONE',len(out),'fulltext',sum(x.get('fulltext_obtained',False) for x in out),flush=True)
