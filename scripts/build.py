#!/usr/bin/env python3
"""Deterministic, offline exports from frozen bibliography and framing inputs."""
from pathlib import Path
import json,html,hashlib
ROOT=Path(__file__).resolve().parent.parent

def bib_escape(s):
 return str(s).replace('\\','\\textbackslash{}').replace('&','\\&').replace('%','\\%').replace('#','\\#').replace('_','\\_')
def render():
 b=json.loads((ROOT/'bibliography.json').read_text());csl=[w['csl'] for w in b['works']];bib=[];ris=[]
 for item in b['works']:
  w=item['csl'];key=item['citekey'];kind=item['kind'];dates=w['issued']['date-parts'][0]
  bt={'preprint':'misc','conference':'inproceedings','journal':'article','report':'techreport'}[kind]
  fields={'title':w['title'],'author':' and '.join(a['family']+', '+a['given'] if 'family' in a else '{'+a['literal']+'}' for a in w['author']),'year':str(dates[0]),'date':'-'.join(str(x).zfill(4 if i==0 else 2) for i,x in enumerate(dates)),'url':w['URL'],'note':w['note']}
  if len(dates)>1:fields['month']=str(dates[1])
  if len(dates)>2:fields['day']=str(dates[2])
  if 'DOI' in w:fields['doi']=w['DOI']
  if 'container-title' in w:fields['booktitle' if kind=='conference' else 'journal']=w['container-title']
  for src,dst in [('publisher','institution' if kind=='report' else 'publisher'),('volume','volume'),('issue','number'),('page','pages'),('number','number'),('archive','archivePrefix'),('archive_location','eprint')]:
   if src in w:fields[dst]=w[src]
  bib.append('@'+bt+'{'+key+',\n'+',\n'.join('  '+k+' = {'+(str(v) if k in ['doi','url'] else bib_escape(v))+'}' for k,v in fields.items())+'\n}')
  tags=[('TY',{'preprint':'UNPB','conference':'CPAPER','journal':'JOUR','report':'RPRT'}[kind]),('ID',key),('TI',w['title'])]
  tags.extend(('AU',a['family']+', '+a['given']) if 'family' in a else ('AU',a['literal']+',') for a in w['author'])
  tags.extend([('PY',str(dates[0])),('DA','/'.join(str(x).zfill(4 if i==0 else 2) for i,x in enumerate(dates))),('UR',w['URL']),('N1',w['note'])])
  for src,dst in [('DOI','DO'),('container-title','T2'),('publisher','PB'),('volume','VL'),('issue','IS')]:
   if src in w:tags.append((dst,w[src]))
  if 'page' in w:
   ps=w['page'].split('-');tags.append(('SP',ps[0]));
   if len(ps)>1:tags.append(('EP',ps[-1]))
  if kind=='report':tags.append(('M1',w['number']))
  tags.append(('ER',''));ris.append('\n'.join(k+'  - '+str(v) for k,v in tags))
 scope=json.loads((ROOT/'metadata.json').read_text())['relevance_and_citation_scope']
 return {'references.csl.json':json.dumps(csl,ensure_ascii=False,indent=2)+'\n','references.bib':'\n\n'.join(bib)+'\n','references.ris':'\n\n'.join(ris)+'\n','references.md':'# Published references\n\n'+'\n\n'.join(s['published_reference'] for s in b['slots'])+'\n','index.html':(ROOT/'sources/index.template.html').read_text().replace('@@SCOPE@@',html.escape(scope)),'README.md':(ROOT/'sources/README-prefix.md').read_text().replace('@@SCOPE@@',scope)+'## Published paper — complete machine-readable text\n\n'+(ROOT/'paper.md').read_text()}
def manifest():
 return ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='checksums.sha256' and '.git' not in p.parts and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo'])
def main():
 for path,value in render().items():(ROOT/path).write_text(value,encoding='utf8')
 (ROOT/'checksums.sha256').write_text(manifest())
if __name__=='__main__':main()
