import json,csv,collections
from pathlib import Path
P=Path('/var/minis/shared/local-agent-research-2026/folo-2026');w=json.load(open(P/'rubric.json'))['weights'];rows=[]
for a in json.load(open(P/'all-2026.json')):
 f=P/'jev-output'/(a['id']+'.json')
 if not f.exists():continue
 j=json.load(open(f));b=j['answers'];row={k:a[k] for k in ['id','title','source','date','url']};row.update({k:b[k]['score'] for k in w});row['score']=round(sum(row[k]*v/5 for k,v in w.items()),2);row['category']=b['category']['choice'];row['method']=j.get('assessment_method','single_fulltext');rows.append(row)
rows.sort(key=lambda x:x['score'],reverse=True)
(P/'scores.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with (P/'scores.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
counts=collections.Counter(r['category'] for r in rows);print('COUNTS',counts)
labels={'direct_local':'直接本地生活','transfer_business':'经营决策可迁移','transfer_agent':'Agent工程可迁移','peripheral':'外围参考','irrelevant':'其他/不相关'}
s=['# 2026六源全年文章评分索引','',f'已评估 {len(rows)} 篇；单次全文及9篇分段汇总分别标记。小分差不应视为可靠排名，Jev评分未作人工校准。','']
for cat,label in labels.items():
 s+=['## '+label,'','|分数|文章|来源|日期|方法|','|---:|---|---|---|---|']
 for r in rows:
  if r['category']==cat:s.append(f"|{r['score']}|[{r['title'].replace('|','／')}](articles/{r['id']}.md)|{r['source']}|{r['date']}|{'分段' if r['method']!='single_fulltext' else '全文'}|")
 print('\n',label);print('\n'.join(f"{r['score']} {r['id']} {r['title']}" for r in rows if r['category']==cat)[:13000])
(P/'INDEX.md').write_text('\n'.join(s));(P/'summary.json').write_text(json.dumps({'assessed':len(rows),'category_counts':counts},ensure_ascii=False,indent=2))
