import {Presentation} from 'file:///C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=Presentation.create({slideSize:{width:1280,height:720}});const s=p.slides.add();const a=s.shapes.add({geometry:'rect',position:{left:0,top:0,width:1,height:1},fill:'none',shadow:'0px 30px 60px #14352B/25'});const v=a.outerShadow;
console.log('values',v.blurRadius,v.distance,v.direction);
