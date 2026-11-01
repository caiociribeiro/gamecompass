// Ferramenta de desenvolvimento: captura somente o motor congelado da etapa27.
import * as esbuild from '../../frontend/node_modules/esbuild/lib/main.js';
import fs from 'node:fs';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const root=fileURLToPath(new URL('../../',import.meta.url));
const directory=mkdtempSync(join(tmpdir(),'gamecompass-parity-'));
const bundle=join(directory,'capture.mjs');
const functions={recommend:['windowsCheck','hardwareChecks','describeMatch','replacementPart','buildRecommendations','hardwareProfileReady','profileReady'],
  affinity:['facetSimilarity','contentAffinity'],upgrades:['replacementOptions']};
try {
  await esbuild.build({stdin:{contents:`
    import fs from 'node:fs';globalThis.__parity=[];
    await import(${JSON.stringify(root+'frontend/tests/recommend.test.ts')});
    await import(${JSON.stringify(root+'frontend/tests/affinity.test.ts')});
    await import(${JSON.stringify(root+'frontend/tests/upgrades.test.ts')});
    process.once('beforeExit',()=>{
      const rows=[...new Map(globalThis.__parity.map(r=>[JSON.stringify(r),r])).values()];
      fs.writeFileSync(${JSON.stringify(root+'backend/tests/fixtures/engine_parity.json')},JSON.stringify(rows)+'\\n');
      console.log('Casos de paridade:',rows.length);
    });`,loader:'ts',resolveDir:root+'frontend'},bundle:true,format:'esm',platform:'node',outfile:bundle,
    plugins:[{name:'capture',setup(build){build.onLoad({filter:/tests[\\/]reference[\\/](?:recommend|affinity|upgrades)\.ts$/},async args=>{
      let source=fs.readFileSync(args.path,'utf8');
      for(const name of functions[args.path.split(/[\\/]/).pop().replace('.ts','')]){
        source=source.replace('export function '+name+'(','function _'+name+'(');
        source+=`\nexport function ${name}(...args){const result=_${name}(...args);globalThis.__parity.push({function:'${name}',args:structuredClone(args),expected:structuredClone(result)});return result;}\n`;
      }
      return {contents:source,loader:'ts'};
    });}}]});
  const result=spawnSync(process.execPath,[bundle],{stdio:'inherit',cwd:root});
  if(result.status!==0)process.exitCode=result.status??1;
} finally {esbuild.stop();rmSync(directory,{recursive:true,force:true});}
