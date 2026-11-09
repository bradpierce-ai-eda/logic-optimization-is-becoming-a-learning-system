/* Independent parser checks. Dependencies: @citation-js/core, plugin-bibtex, plugin-csl, plugin-ris 0.9.0. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {Cite}=require('@citation-js/core');
require('@citation-js/plugin-bibtex');require('@citation-js/plugin-csl');require('@citation-js/plugin-ris');
const root=path.resolve(__dirname,'..');
const works=JSON.parse(fs.readFileSync(path.join(root,'bibliography.json'),'utf8')).works;
for(const file of ['references.bib','references.csl.json','references.ris']){
 const parsed=new Cite(fs.readFileSync(path.join(root,file),'utf8')).data;
 assert.equal(parsed.length,works.length);
 for(let i=0;i<works.length;i++){
  const expected=works[i].csl,actual=parsed[i];
  for(const field of ['id','title','author','issued','URL','DOI'])assert.deepStrictEqual(actual[field],expected[field],file+': '+expected.id+' '+field);
 }
 console.log('PASS: '+file+' — 28 stable IDs, exact titles/authors, full dates, URLs and DOIs.');
}
