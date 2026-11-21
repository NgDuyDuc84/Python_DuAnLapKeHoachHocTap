import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from 'file:///C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import design from './design.mjs';
const b='D:/Python_DuAnLapKeHoachHocTap/.pptx-hero-nhom7';const p=JSON.parse(await fs.readFile(b+'/before.json','utf8'));const map=JSON.parse(await fs.readFile(b+'/asset-map.json','utf8'));
for(const im of p.images){im.data=new Uint8Array(await fs.readFile(b+'/'+map[im.id]));delete im.uri;}
const presentation=Presentation.load(p);console.log(await design({presentation}));
await fs.writeFile(b+'/deck.json',JSON.stringify(presentation.toProto()));
await (await PresentationFile.exportPptx(presentation)).save(b+'/candidate.pptx');
for(const n of [0,9]){const png=await presentation.export({slide:presentation.slides.getItem(n),format:'png',scale:1});await fs.writeFile(b+'/slide-'+(n+1)+'.png',new Uint8Array(await png.arrayBuffer()));}
console.log('Exported and rendered both slides');
