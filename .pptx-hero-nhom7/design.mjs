import fs from 'node:fs/promises';
const B='D:/Python_DuAnLapKeHoachHocTap/.pptx-hero-nhom7';
const C={bg:'#F6F1E4',ink:'#14352B',green:'#1E6B54',body:'#3B4A44',soft:'#DDEBE3',ring:'#BFD8CB',faint:'#E2D9BF',gold:'#E9C46A',pale:'#F3DFA6'};
export default async function design({presentation}){
 const source=JSON.parse(await fs.readFile(B+'/source.json','utf8')); const calendarBytes=new Uint8Array(await fs.readFile(B+'/image.png'));
 const map=JSON.parse(await fs.readFile(B+'/asset-map.json','utf8'));
 function rect(s,x,y,w,h,fill,r=0,rotation=0){return s.shapes.add({geometry:r?'roundRect':'rect',position:{left:x,top:y,width:w,height:h,rotation},fill,line:{fill:'none',width:0},...(r?{borderRadius:r}:{})});}
 function T(s,t,x,y,w,h,size,bold=false,color=C.body,line=1.2){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=t;a.text.style={fontFamily:'Arial',fontSize:size,bold,color,lineSpacing:line,wrap:'none',insets:0,autoFit:'none'};return a;}
 function panel(s,left){const x=left?0:704,w=576,h=720,r=40,k=.5522847498;let q;
  if(left)q=[{moveTo:{x:0,y:0}},{lineTo:{x:w-r,y:0}},{cubicBezTo:{x1:w-r+r*k,y1:0,x2:w,y2:r-r*k,x:w,y:r}},{lineTo:{x:w,y:h-r}},{cubicBezTo:{x1:w,y1:h-r+r*k,x2:w-r+r*k,y2:h,x:w-r,y:h}},{lineTo:{x:0,y:h}},{close:{}}];
  else q=[{moveTo:{x:r,y:0}},{lineTo:{x:w,y:0}},{lineTo:{x:w,y:h}},{lineTo:{x:r,y:h}},{cubicBezTo:{x1:r-r*k,y1:h,x2:0,y2:h-r+r*k,x:0,y:h-r}},{lineTo:{x:0,y:r}},{cubicBezTo:{x1:0,y1:r-r*k,x2:r-r*k,y2:0,x:r,y:0}},{close:{}}];
  s.shapes.add({geometry:'custom',position:{left:x,top:0,width:w,height:h},fill:C.soft,line:{fill:'none',width:0},customPaths:[{width:w,height:h,commands:q}]});
 }
 function ring(s,cx,cy,r,bounds,color){const [x0,y0,x1,y1]=bounds,w=x1-x0,h=y1-y0;let commands=[],active=false;
  function inside(p){return p.x>=x0&&p.x<=x1&&p.y>=y0&&p.y<=y1;}
  function clip(a,b){let t0=0,t1=1,dx=b.x-a.x,dy=b.y-a.y;for(const [p,q]of[[-dx,a.x-x0],[dx,x1-a.x],[-dy,a.y-y0],[dy,y1-a.y]]){if(Math.abs(p)<1e-9){if(q<0)return null;}else{const t=q/p;if(p<0){if(t>t1)return null;t0=Math.max(t0,t);}else{if(t<t0)return null;t1=Math.min(t1,t);}}}return[{x:a.x+t0*dx,y:a.y+t0*dy},{x:a.x+t1*dx,y:a.y+t1*dy}];}
  let prev={x:cx+r,y:cy};
  for(let j=1;j<=1440;j++){const angle=j/1440*Math.PI*2,p={x:cx+r*Math.cos(angle),y:cy+r*Math.sin(angle)},part=clip(prev,p);if(part){let[a,b]=part;if(!active||!inside(prev))commands.push({moveTo:{x:a.x-x0,y:a.y-y0}});commands.push({lineTo:{x:b.x-x0,y:b.y-y0}});active=true;}else active=false;prev=p;}
  s.shapes.add({geometry:'custom',position:{left:x0,top:y0,width:w,height:h},fill:'none',line:{fill:color,width:2},customPaths:[{width:w,height:h,commands}]});
 }
 function rhythm(s,x,baseline,scale=1){[20,36,28,52,32,44,24].forEach((h,i)=>rect(s,x+i*22*scale,baseline-h*scale,14*scale,h*scale,[1,3,5].includes(i)?C.gold:C.green,7*scale));}
 function floating(s,left){for(const[x,y,size,a,fill]of[[750,100,32,-10,C.gold],[1200,98,24,12,C.pale],[744,612,26,15,C.pale],[1196,616,36,-12,C.gold],[1244,330,24,8,C.gold]])rect(s,left?1280-x-size:x,y,size,size,fill,7,a*(left?-1:1));}
 function calendar(s,left){const ids=new Set(presentation.toProto().images.map(a=>a.id));const im=s.images.add({blob:calendarBytes,contentType:'image/png',alt:'Ảnh lịch bàn Nhịp Học',position:{left:left?18:722,top:150,width:540,height:420},fit:'contain'});im.crop={left:40/1254,top:210/1254,right:44/1254,bottom:134/1254};im.rotation=left?4:-4;
  const probe=s.shapes.add({geometry:'rect',position:{left:0,top:0,width:1,height:1},fill:'none',line:{fill:'none',width:0},shadow:'0px 30px 60px #14352B/25'});im.outerShadow={blurRadius:60,distance:30,direction:90,color:"rgba(20,53,43,0.25)"};probe.delete();for(const a of presentation.toProto().images)if(!ids.has(a.id))map[a.id]='image.png';return im;
 }
 for(const idx of [0,9]){const s=presentation.slides.getItem(idx);for(const a of [...s.shapes.items])a.delete();for(const a of [...s.images.items])a.delete();s.background.fill=C.bg;const left=idx===9;
  ring(s,left?1280:0,720,250,left?[576,0,1280,720]:[0,0,704,720],C.faint);panel(s,left);
  for(const r of [210,310,410])ring(s,left?288:992,360,r,left?[0,0,576,720]:[704,0,1280,720],C.ring);
  floating(s,left);calendar(s,left);
  if(idx===0){
   const title=T(s,'Nhịp Học',64,128,620,174,128,true,C.ink,1);
   title.text=[{runs:[{run:'Nhịp ',style:{typeface:'Arial',fontSize:'128px',bold:true,color:C.ink,characterSpacing:-192}},{run:'Học',style:{typeface:'Arial',fontSize:'128px',bold:true,color:C.green,characterSpacing:-192}}]}];
   rhythm(s,64,362);
   T(s,'Ứng dụng lập kế hoạch\nhọc tập cá nhân',64,400,600,96,32,false,C.body,1.4);
   const pill=rect(s,64,544,164,56,C.green,28);pill.text='Nhóm 7';pill.text.style={fontFamily:'Arial',fontSize:26,bold:true,color:'#FFFFFF',alignment:'center',verticalAlignment:'middle',lineSpacing:1,insets:{left:28,right:28,top:10,bottom:10},wrap:'none',autoFit:'none'};
  }else{
   const a=source[9];T(s,a[0],624,30,608,110,80,true,C.ink,1);rhythm(s,624,202);T(s,a[a.length-1],624,226,608,40,28,true,C.green,1.2);
   T(s,a[2],624,286,520,40,28,true,C.green,1.2);T(s,a[1],1196,294,36,26,16,true,'#5C6B64');T(s,a[3],624,330,608,136,22,false,C.body,1.2);
   T(s,a[5],624,486,520,40,28,true,C.green,1.2);T(s,a[4],1196,494,36,26,16,true,'#5C6B64');T(s,a[6],624,532,608,136,22,false,C.body,1.2);
  }
 }
 await fs.writeFile(B+'/asset-map.json',JSON.stringify(map));
 return{changedSlides:[1,10],images:presentation.toProto().images.length};
}



