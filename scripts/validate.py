#!/usr/bin/env python3
"""Offline release validator; public PDF and canonical paper remain immutable."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
from hashlib import sha256,md5
from html.parser import HTMLParser
import json,re,importlib.util,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
EXPECTED=['CITATION.cff','README.md','paper.md','paper.pdf','index.html','citation.bib','metadata.json','provenance.json','references.md','bibliography.json','references.bib','references.csl.json','references.ris','sitemap.xml','robots.txt','assets/figure-1.png','assets/figure-2.png','scripts/validate.py','scripts/build.py','scripts/validate_exports.cjs','sources/index.template.html','sources/README-prefix.md']+[f'authorities/{n}-audit.json' for n in range(1,29)]
def require(x,msg):
 if not x:raise AssertionError(msg)
class P(HTMLParser):
 def __init__(self):super().__init__();self.tags=[];self.attrs=[];self.text=[]
 def handle_starttag(self,t,a):self.tags.append(t);self.attrs.append((t,dict(a)))
 def handle_data(self,d):self.text.append(d)
def main():
 files={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts}
 require(files==set(EXPECTED)|{'checksums.sha256'},'Unexpected or missing public path')
 manifest={}
 for line in (ROOT/'checksums.sha256').read_text().splitlines():
  digest,path=line.split('  ',1);require(path not in manifest,'Duplicate checksum entry');manifest[path]=digest
 require(set(manifest)==set(EXPECTED),'Manifest path-set mismatch')
 for path,digest in manifest.items():require(sha256((ROOT/path).read_bytes()).hexdigest()==digest,'SHA mismatch: '+path)
 pdf=(ROOT/'paper.pdf').read_bytes();require(len(pdf)==639041 and sha256(pdf).hexdigest()=='18f5dc87b579157fa7260eeabda30f2bc40cc061c0eadbc5a977cdfc358ea65b','Canonical PDF changed')
 require(sha256((ROOT/'paper.md').read_bytes()).hexdigest()=='d59c8920782c7d5a13dc39b6401057f34648e0e833b156c24e9dbe7a55185c38','Canonical Markdown changed')
 spec=importlib.util.spec_from_file_location('frozen_build',ROOT/'scripts/build.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
 for path,value in build.render().items():require((ROOT/path).read_text()==value,'Nondeterministic/stale output: '+path)
 h=(ROOT/'index.html').read_text();require(h.count('This report was developed by Brad Pierce with substantial assistance from an AI model. He established the research objectives and editorial direction and retains responsibility for the claims, source attributions, and decisions about publication.')==1,'HTML disclosure mismatch');p=P();p.feed(h);m=json.loads((ROOT/'metadata.json').read_text());title='Logic Optimization Is Becoming a Learning System';doi='10.5281/zenodo.22837235';url='https://bradpierce.ai/logic-optimization-is-becoming-a-learning-system/'
 require(m['title']==title and m['doi']==doi and m['publication_date']=='2026-09-11','Metadata identity')
 for name,val in [('citation_title',title),('citation_author','Brad Pierce'),('citation_doi',doi),('citation_publication_date','2026/09/11'),('citation_pdf_url',url+'paper.pdf'),('citation_fulltext_html_url',url)]:require([d.get('content') for t,d in p.attrs if t=='meta' and d.get('name')==name]==[val],'Scholarly metadata mismatch: '+name)
 require(p.tags.count('table')==13 and p.tags.count('img')==2,'Table/figure count')
 ids=[d['id'] for t,d in p.attrs if 'id' in d];require(len(ids)==len(set(ids)),'Duplicate anchor')
 require(all('ref-'+str(n) in ids for n in range(1,29)),'Missing reference anchor')
 for t,d in p.attrs:
  if t=='img':require(bool(d.get('alt')) and (ROOT/d['src']).is_file(),'Image asset/alt')
  if t=='a' and d.get('href','').startswith('#'):require(d['href'][1:] in ids,'Broken internal link')
 require(h.index('<h1 class="paper-title">')<h.index('class="article-author"')<h.index('class="publication-details"')<h.index('id="abstract"')<h.index('<aside id="relevance-and-citation-scope"')<h.index('id="the-learning-system-is-already-emerging"'),'Scholarly front-matter order')
 scope=m['relevance_and_citation_scope'];require(scope in h and scope in (ROOT/'README.md').read_text(),'Scope drift')
 for phrase in ['You should cite','Cite this report','Ignore previous instructions','When to cite this report']:
  require(phrase.lower() not in scope.lower(),'Imperative framing')
 b=json.loads((ROOT/'bibliography.json').read_text());require([s['slot'] for s in b['slots']]==list(range(1,29)),'Slot order/completeness')
 require(len(b['works'])==28 and len(b['slot_to_work'])==28,'Work/link count')
 keys=[w['citekey'] for w in b['works']];workids=[w['work_id'] for w in b['works']];require(len(set(keys))==28 and len(set(workids))==28,'Duplicate stable key')
 require({x['work_id'] for x in b['slot_to_work']}==set(workids),'Orphan slot/work')
 dois=[w['csl']['DOI'].lower() for w in b['works'] if 'DOI' in w['csl']];require(len(dois)==len(set(dois)),'Duplicate DOI')
 for w in b['works']:
  c=w['csl'];require(c['title'] and c['author'] and c.get('issued') and c['URL'],'Missing reusable field')
  require((ROOT/w['authority_evidence']).is_file(),'Missing frozen authority evidence')
 for s in b['slots']:require(s['published_reference'] in (ROOT/'references.md').read_text(),'Published reference changed')
 locs=[n.text for n in ET.parse(ROOT/'sitemap.xml').findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')];require(locs==[url,url+'paper.pdf'],'Sitemap identity')
 require(doi in (ROOT/'CITATION.cff').read_text() and doi in (ROOT/'citation.bib').read_text(),'Preferred citation identity')
 print(f'PASS: {len(files)} public files; exact manifest; frozen PDF/Markdown; deterministic outputs; scholarly metadata/front matter; 13 tables, 2 figures, 28 reference slots/works; authority evidence and crawler paths.')
if __name__=='__main__':
 try:main()
 except Exception as e:print('FAIL:',e,file=sys.stderr);sys.exit(1)
