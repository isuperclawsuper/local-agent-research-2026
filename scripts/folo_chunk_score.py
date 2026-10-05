import json,subprocess,concurrent.futures,collections
from pathlib import Path
P=Path('/var/minis/shared/local-agent-research-2026/folo-2026');E='/var/minis/skills/jev-eval/scripts/evaluate.mjs'
tasks=[]; articles=[]
for a in json.load(open(P/'all-2026.json')):
 if (P/'jev-output'/(a['id']+'.json')).exists():continue
 template=json.load(open(P/'jev-input'/(a['id']+'.json')));parts=[a['text'][i:i+6500] for i in range(0,len(a['text']),6500)];articles.append((a,parts))
 for i,t in enumerate(parts):
  ident=a['id']+f'-part-{i+1:02}'; j=json.loads(json.dumps(template));j['state']['article']['text']=t;j['state']['article']['chars']=len(t);j['state']['article']['chunk_index']=i+1;j['state']['article']['chunk_count']=len(parts);j['state']['research_context']+=' 当前是完整长文的连续分段，只判断当前段落证据。';j['context']='这是超长文章完整连续分段之一，只评估当前段落呈现的证据，不假定缺失内容。\n标题：'+a['title']+'\n分段：'+str(i+1)+'/'+str(len(parts))+'\n'+t
  (P/'jev-input'/(ident+'.json')).write_text(json.dumps(j,ensure_ascii=False));tasks.append(ident)
def run(ident):
 p=P/'jev-output'/(ident+'.json')
 if p.exists():return
 for attempt in range(3):
  r=subprocess.run(['node',E,str(P/'jev-input'/(ident+'.json'))],capture_output=True,text=True,timeout=180)
  if r.returncode==0:
   json.loads(r.stdout);p.write_text(r.stdout);print('CHUNK',ident,flush=True);return
 raise RuntimeError(ident)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(run,tasks))
for a,parts in articles:
 js=[json.load(open(P/'jev-output'/(a['id']+f'-part-{i+1:02}.json'))) for i in range(len(parts))];answers={};keys=js[0]['answers'].keys()
 for k in keys:
  v=js[0]['answers'][k]
  if 'score' in v:answers[k]={'score':round(sum(j['answers'][k]['score']*len(parts[i]) for i,j in enumerate(js))/sum(map(len,parts)),4)}
  elif 'choice' in v:
   counts=collections.Counter(j['answers'][k]['choice'] for j in js);answers[k]={'choice':counts.most_common(1)[0][0]}
  elif 'value' in v:answers[k]={'value':all(j['answers'][k]['value'] for j in js)}
  else:answers[k]=v
 out={'answers':answers,'assessment_method':'full_text_chunked_length_weighted_mean','parts':len(parts),'aggregation_note':'连续6500字符无遗漏分段；评分按段长加权均值，分类按多数段。局部证据可能被稀释，不能等同整体判断。','usage':{'totalTokens':sum((j.get('usage',{}).get('totalTokens') or 0) for j in js)}}
 (P/'jev-output'/(a['id']+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2));print('AGGREGATED',a['title'],flush=True)
