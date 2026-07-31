import * as THREE from '../vendor/three.module.min.js';

const canvas=document.getElementById('game');
const menu=document.getElementById('menu');
const gameover=document.getElementById('gameover');
const pausePanel=document.getElementById('pause');
const pauseToggle=document.getElementById('pause-toggle');
const scoreEl=document.getElementById('score');
const bestEl=document.getElementById('best');
const finalScoreEl=document.getElementById('final-score');
const WORLD_HALF=8, AHEAD=30, BEHIND=7, HOP_TIME=.16;
const palette={sky:0x92e8e0,grass:0x62cf79,grassDark:0x46ad60,road:0x50566b,roadEdge:0x35394b,cream:0xfff7d6,gold:0xf7d154,purple:0x7b45da,cyan:0x55f3dd,ink:0x20113f};

function loadBest(){try{return Math.max(0,parseInt(localStorage.getItem('roadHop.best')||'0',10)||0)}catch{return 0}}
function saveBest(value){try{localStorage.setItem('roadHop.best',String(value))}catch{}}
function material(color){return new THREE.MeshLambertMaterial({color})}
function box(w,h,d,color){const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material(color));mesh.castShadow=true;mesh.receiveShadow=true;return mesh}
function disposeObject(object){if(object.geometry)object.geometry.dispose();if(object.material){if(Array.isArray(object.material)){for(let i=0;i<object.material.length;i++)object.material[i].dispose()}else object.material.dispose()}for(let i=0;i<object.children.length;i++)disposeObject(object.children[i])}
function seeded(row,salt=0){let x=Math.imul(row+173+salt*97,2654435761);x^=x>>>15;x=Math.imul(x,2246822519);return((x^(x>>>13))>>>0)/4294967296}

const scene=new THREE.Scene();scene.background=new THREE.Color(palette.sky);scene.fog=new THREE.Fog(palette.sky,20,46);
const camera=new THREE.OrthographicCamera(-9,9,6,-6,.1,100);camera.position.set(10,12,10);
const cameraTarget=new THREE.Vector3();
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;
scene.add(new THREE.HemisphereLight(0xffffff,0x52633d,2.25));
const sun=new THREE.DirectionalLight(0xfff3c4,3.5);sun.position.set(-8,16,10);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-16;sun.shadow.camera.right=16;sun.shadow.camera.top=18;sun.shadow.camera.bottom=-18;scene.add(sun);
const world=new THREE.Group();scene.add(world);

function createPip(){const group=new THREE.Group();const body=box(.72,.68,.72,palette.purple);body.position.y=.64;group.add(body);const head=box(.66,.45,.62,0x925ff0);head.position.set(0,1.16,.02);group.add(head);const visor=new THREE.Mesh(new THREE.BoxGeometry(.5,.18,.04),new THREE.MeshBasicMaterial({color:palette.cyan}));visor.position.set(0,1.19,.34);group.add(visor);const antenna=box(.09,.26,.09,palette.ink);antenna.position.y=1.55;group.add(antenna);const bulb=box(.18,.18,.18,palette.gold);bulb.position.y=1.72;group.add(bulb);for(const x of[-.23,.23]){const foot=box(.23,.16,.38,palette.gold);foot.position.set(x,.14,.08);group.add(foot)}group.rotation.y=Math.PI;return group}
const pip=createPip();scene.add(pip);

const lanes=[];const vehicles=[];
const player={row:0,x:0,moving:null};
let state='MENU',score=0,best=loadBest(),furthest=0,forceCrash=false,cameraRow=3,lastTime=0,audio=null;
bestEl.textContent=best;

function laneType(row){if(row<=1||row%5===0)return'grass';return seeded(row)>.34?'road':'grass'}
function addTree(group,row,x,blockers){const trunk=box(.28,.65,.28,0x805335);trunk.position.set(x,.22,-row);group.add(trunk);const crown=box(.78,.82,.78,seeded(row,x+20)>.5?0x2f9f58:0x3bbf68);crown.position.set(x,.9,-row);group.add(crown);blockers.add(x)}
function addLamp(group,row,x){const pole=box(.09,1.25,.09,0x34344a);pole.position.set(x,.55,-row);group.add(pole);const light=box(.28,.22,.28,palette.gold);light.position.set(x,1.24,-row);group.add(light)}
function createCar(row,index,direction,speed){const colors=[0xff6b58,0x45b7e8,0xf2c94c,0xe96fd1];const group=new THREE.Group();const body=box(1.12,.42,.68,colors[(row+index)%colors.length]);body.position.y=.42;group.add(body);const cabin=box(.55,.32,.58,0xd9f8ff);cabin.position.set(-direction*.08,.75,0);group.add(cabin);for(const dx of[-.36,.36])for(const dz of[-.34,.34]){const wheel=box(.19,.2,.1,0x1c1b28);wheel.position.set(dx,.24,dz);group.add(wheel)}group.position.set(-WORLD_HALF+seeded(row,index)*16,0,-row);group.rotation.y=direction<0?Math.PI:0;world.add(group);const vehicle={mesh:group,row,x:group.position.x,direction,speed,width:1.15};vehicles.push(vehicle);return vehicle}
function makeLane(row){const type=laneType(row);const group=new THREE.Group();const blockers=new Set();const base=box(18,type==='road'?.22:.42,1,type==='road'?palette.road:(row%2?palette.grass:palette.grassDark));base.position.set(0,type==='road'?-.12:-.22,-row);group.add(base);
 if(type==='road'){
  const edge1=box(18,.05,.06,palette.roadEdge);edge1.position.set(0,.02,-row-.46);group.add(edge1);const edge2=edge1.clone();edge2.position.z=-row+.46;group.add(edge2);
  for(let x=-7.4;x<8;x+=2){const mark=box(.85,.025,.055,palette.cream);mark.position.set(x,.025,-row);group.add(mark)}
  const direction=seeded(row,2)>.5?1:-1;const speed=1.8+seeded(row,3)*1.8+Math.min(row,80)*.012;const count=2+(seeded(row,4)>.5?1:0);for(let i=0;i<count;i++){const car=createCar(row,i,direction,speed);car.x=-7+i*(16/count)+seeded(row,i+9)*1.2;car.mesh.position.x=car.x}
 }else if(row>1){const count=1+Math.floor(seeded(row,5)*3);for(let i=0;i<count;i++){let x=-6+Math.floor(seeded(row,i+12)*13);if(x===0&&row<4)x=3;while(blockers.has(x))x=Math.min(7,x+1);addTree(group,row,x,blockers)}if(row%5===0){addLamp(group,row,-7.35);addLamp(group,row,7.35)}}
 world.add(group);const lane={row,type,group,blockers};lanes.push(lane);return lane}
function clearWorld(){while(world.children.length){const child=world.children[world.children.length-1];world.remove(child);disposeObject(child)}lanes.length=0;vehicles.length=0}
function ensureWorld(center){const min=Math.max(-5,center-BEHIND),max=center+AHEAD;for(let row=min;row<=max;row++)if(!lanes.some(l=>l.row===row))makeLane(row);for(let i=lanes.length-1;i>=0;i--){if(lanes[i].row<min||lanes[i].row>max){world.remove(lanes[i].group);disposeObject(lanes[i].group);lanes.splice(i,1)}}for(let i=vehicles.length-1;i>=0;i--){if(vehicles[i].row<min||vehicles[i].row>max){world.remove(vehicles[i].mesh);disposeObject(vehicles[i].mesh);vehicles.splice(i,1)}}}
function laneAt(row){return lanes.find(l=>l.row===row)}
function updateUI(){scoreEl.textContent=score;bestEl.textContent=best;finalScoreEl.textContent=score}
function setState(next){state=next;game.state=next;menu.classList.toggle('hidden',next!=='MENU');gameover.classList.toggle('hidden',next!=='GAME_OVER');pausePanel.classList.toggle('hidden',next!=='PAUSED');pauseToggle.classList.toggle('hidden',next!=='PLAYING')}
function start(){clearWorld();player.row=0;player.x=0;player.moving=null;score=0;furthest=0;forceCrash=false;cameraRow=3;pip.position.set(0,0,0);pip.rotation.set(0,Math.PI,0);ensureWorld(0);updateUI();setState('PLAYING')}
function targetFor(direction){const map={forward:[0,1,Math.PI],back:[0,-1,0],left:[-1,0,-Math.PI/2],right:[1,0,Math.PI/2]};return map[direction]}
function move(direction){if(state!=='PLAYING'||player.moving)return false;const delta=targetFor(direction);if(!delta)return false;const tx=player.x+delta[0],tr=player.row+delta[1];if(tx<-7||tx>7||tr<0)return false;ensureWorld(tr);const lane=laneAt(tr);if(lane&&lane.blockers.has(tx))return false;player.moving={fromX:player.x,fromRow:player.row,toX:tx,toRow:tr,t:0,angle:delta[2]};pip.rotation.y=delta[2];playTone(310,.045);return true}
function finishMove(m){player.x=m.toX;player.row=m.toRow;player.moving=null;if(player.row>furthest){furthest=player.row;score=furthest;updateUI();ensureWorld(player.row)}}
function collide(){if(forceCrash)return true;const lane=laneAt(player.row);if(!lane||lane.type!=='road'||player.moving)return false;for(let i=0;i<vehicles.length;i++){const v=vehicles[i];if(v.row===player.row&&Math.abs(v.x-player.x)<(v.width+.56)/2)return true}return false}
function die(){if(state!=='PLAYING')return;player.moving=null;if(score>best){best=score;saveBest(best)}updateUI();setState('GAME_OVER');playTone(95,.22)}
function update(dt){dt=Math.min(Math.max(dt,0),.1);if(state!=='PLAYING')return;
 for(let i=0;i<vehicles.length;i++){const v=vehicles[i];v.x+=v.speed*v.direction*dt;if(v.x>WORLD_HALF+2)v.x=-WORLD_HALF-2;if(v.x<-WORLD_HALF-2)v.x=WORLD_HALF+2;v.mesh.position.x=v.x;for(let part=2;part<v.mesh.children.length;part++)v.mesh.children[part].rotation.z-=dt*v.speed*2}
 if(player.moving){const m=player.moving;m.t+=dt;const p=Math.min(1,m.t/HOP_TIME);const smooth=p*p*(3-2*p);pip.position.x=THREE.MathUtils.lerp(m.fromX,m.toX,smooth);pip.position.z=-THREE.MathUtils.lerp(m.fromRow,m.toRow,smooth);pip.position.y=Math.sin(p*Math.PI)*.62;if(p>=1){pip.position.set(m.toX,0,-m.toRow);finishMove(m)}}
 if(collide())die();cameraRow+=((player.row+3)-cameraRow)*Math.min(1,dt*4.5)}
function render(t){cameraTarget.set(0,0,-cameraRow);camera.position.set(10,12,10-cameraRow);camera.lookAt(cameraTarget);if(state==='MENU')pip.position.y=Math.sin(t*.002)*.05;renderer.render(scene,camera)}
function resize(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);const aspect=w/h;const view=12;camera.left=-view*aspect/2;camera.right=view*aspect/2;camera.top=view/2;camera.bottom=-view/2;camera.updateProjectionMatrix()}
function unlockAudio(){if(audio)return;const AC=window.AudioContext||window.webkitAudioContext;if(AC)audio=new AC()}
function playTone(freq,duration){if(!audio||audio.state!=='running')return;const osc=audio.createOscillator(),gain=audio.createGain();osc.type='square';osc.frequency.value=freq;gain.gain.setValueAtTime(.035,audio.currentTime);gain.gain.exponentialRampToValueAtTime(.001,audio.currentTime+duration);osc.connect(gain).connect(audio.destination);osc.start();osc.stop(audio.currentTime+duration)}
function togglePause(){if(state==='PLAYING')setState('PAUSED');else if(state==='PAUSED')setState('PLAYING')}
function onKey(event){const key=event.key.toLowerCase();const dirs={arrowup:'forward',w:'forward',arrowdown:'back',s:'back',arrowleft:'left',a:'left',arrowright:'right',d:'right'};if(dirs[key]){event.preventDefault();move(dirs[key])}else if(key==='p'||key==='escape'){event.preventDefault();togglePause()}else if((key===' '||key==='enter')&&(state==='MENU'||state==='GAME_OVER')){event.preventDefault();unlockAudio();start()}}
let pointerStart=null;
function pointerDown(e){if(pointerStart)return;pointerStart={id:e.pointerId,x:e.clientX,y:e.clientY};unlockAudio();if(canvas.setPointerCapture)try{canvas.setPointerCapture(e.pointerId)}catch{}}
function clearPointer(e){if(pointerStart&&(e.pointerId===pointerStart.id||e.pointerId===undefined))pointerStart=null}
function pointerUp(e){if(!pointerStart||e.pointerId!==pointerStart.id)return;const start=pointerStart;clearPointer(e);if(canvas.releasePointerCapture)try{canvas.releasePointerCapture(e.pointerId)}catch{}const dx=e.clientX-start.x,dy=e.clientY-start.y;if(Math.max(Math.abs(dx),Math.abs(dy))<20)return;move(Math.abs(dx)>Math.abs(dy)?(dx>0?'right':'left'):(dy>0?'back':'forward'))}
addEventListener('keydown',onKey);canvas.addEventListener('pointerdown',pointerDown);canvas.addEventListener('pointerup',pointerUp);canvas.addEventListener('pointercancel',clearPointer);addEventListener('resize',resize);
document.getElementById('start').addEventListener('click',()=>{unlockAudio();start()});document.getElementById('retry').addEventListener('click',()=>{unlockAudio();start()});document.getElementById('resume').addEventListener('click',togglePause);pauseToggle.addEventListener('click',togglePause);
resize();ensureWorld(0);
const game={ready:true,state,THREE_REVISION:THREE.REVISION,scene,camera,renderer,pip,player,lanes,vehicles,score,best,start,move,togglePause,debug:{advance(seconds){let left=seconds;while(left>0){const step=Math.min(.05,left);update(step);left-=step}},blockCell(row,x){ensureWorld(row);laneAt(row).blockers.add(x)},clearBlockers(row){const lane=laneAt(row);if(lane)lane.blockers.clear()},forceCrash(){forceCrash=true}}};
Object.defineProperties(game,{score:{get:()=>score},best:{get:()=>best}});window.__game=game;setState('MENU');updateUI();
function frame(t){const dt=lastTime?Math.min((t-lastTime)/1000,.1):0;lastTime=t;update(dt);render(t);requestAnimationFrame(frame)}requestAnimationFrame(frame);
