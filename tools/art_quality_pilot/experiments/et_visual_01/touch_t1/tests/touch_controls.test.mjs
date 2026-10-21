import {test} from 'node:test';
import assert from 'node:assert/strict';
import {attachTouchControls,HOLD_PULSE_MS} from '../touch_controls.js';

class FakeTarget {
  listeners=new Map();
  addEventListener(type,callback){this.listeners.set(type,[...(this.listeners.get(type)||[]),callback]);}
  dispatch(type,fields={}){
    const event={pointerId:fields.pointerId??1,pointerType:fields.pointerType??'touch',button:fields.button??0,
      detail:fields.detail??1,preventDefault(){this.prevented=true;},...fields};
    for(const handler of this.listeners.get(type)||[])handler(event);
    return event;
  }
}
class FakeButton extends FakeTarget {
  constructor(code){super();this.dataset={code};this.classes=new Set();this.classList={toggle:(name,on)=>on?this.classes.add(name):this.classes.delete(name)};}
  setPointerCapture(id){this.lastCapture=id;}
}
function fixture(){
  const buttons=['ArrowLeft','ArrowRight','Space','ShiftLeft','KeyE'].map(code=>new FakeButton(code));
  const root={querySelectorAll:()=>buttons};
  const keys=new Set();const host=new FakeTarget(), doc=new FakeTarget();doc.hidden=false;
  let now=0, id=1;const timers=new Map();
  const clock=()=>now;
  const after=(cb,delay)=>{const token=id++;timers.set(token,{cb,at:now+delay});return token;};
  const cancel=token=>timers.delete(token);
  const tick=(ms)=>{now+=ms;for(const [token,item] of [...timers])if(item.at<=now){timers.delete(token);item.cb();}};
  const controls=attachTouchControls({root,keys,host,documentRoot:doc,clock,after,cancel});
  const btn=code=>buttons.find(b=>b.dataset.code===code);
  return {btn,keys,host,doc,controls,tick,timers};
}
test('hold direction, independent jump finger, short tap survives one game frame',()=>{
  const f=fixture();f.btn('ArrowRight').dispatch('pointerdown',{pointerId:11});f.tick(15);
  f.btn('Space').dispatch('pointerdown',{pointerId:12});
  assert.deepEqual([...f.keys].sort(),['ArrowRight','Space']);
  f.tick(10);f.btn('Space').dispatch('pointerup',{pointerId:12});
  assert.equal(f.keys.has('Space'),true);
  f.tick(HOLD_PULSE_MS);assert.deepEqual([...f.keys],['ArrowRight']);
  f.btn('ArrowRight').dispatch('pointerup',{pointerId:11}); assert.equal(f.keys.size,0);
});
test('release direction is immediate, cancel and lost capture do not strand keys',()=>{
  const f=fixture();f.btn('ArrowLeft').dispatch('pointerdown',{pointerId:1});f.btn('ShiftLeft').dispatch('pointerdown',{pointerId:2});
  f.btn('ArrowLeft').dispatch('pointercancel',{pointerId:1});
  assert.deepEqual([...f.keys],['ShiftLeft']);
  f.btn('ShiftLeft').dispatch('lostpointercapture',{pointerId:2});
  assert.equal(f.keys.size,0);assert.equal(f.timers.size,0);
});
test('multiple touches on one code do not release each other',()=>{
  const f=fixture();f.btn('ArrowLeft').dispatch('pointerdown',{pointerId:1});f.btn('ArrowLeft').dispatch('pointerdown',{pointerId:2});
  f.btn('ArrowLeft').dispatch('pointerup',{pointerId:1});assert.equal(f.keys.has('ArrowLeft'),true);
  f.btn('ArrowLeft').dispatch('pointerup',{pointerId:2});assert.equal(f.keys.has('ArrowLeft'),false);
});
test('window blur, orientation and pagehide cancel queued pulses',()=>{
  for(const event of ['blur','orientationchange','pagehide']){
    const f=fixture();f.btn('KeyE').dispatch('pointerdown',{pointerId:1});f.tick(6);
    f.btn('KeyE').dispatch('pointerup',{pointerId:1}); assert.ok(f.timers.size);
    f.host.dispatch(event);assert.equal(f.keys.size,0);assert.equal(f.timers.size,0);
    f.tick(200);assert.equal(f.keys.size,0);
  }
});
test('hidden document and manual mode change clear simultaneous buttons',()=>{
  const f=fixture();f.btn('ArrowLeft').dispatch('pointerdown',{pointerId:4});f.btn('Space').dispatch('pointerdown',{pointerId:5});
  f.doc.hidden=true;f.doc.dispatch('visibilitychange');assert.equal(f.keys.size,0);
  f.btn('ArrowRight').dispatch('pointerdown',{pointerId:6});f.controls.clear();assert.equal(f.keys.size,0);
});
test('keyboard and assistive click(detail=0) creates one short pulse',()=>{
  const f=fixture();f.btn('Space').dispatch('click',{detail:0});assert.equal(f.keys.has('Space'),true);
  f.tick(HOLD_PULSE_MS+1);assert.equal(f.keys.has('Space'),false);
  f.btn('Space').dispatch('click',{detail:1});assert.equal(f.keys.has('Space'),false);
});
test('ignore non-left mouse button and keyboard click does not duplicate touch',()=>{
  const f=fixture();f.btn('Space').dispatch('pointerdown',{pointerType:'mouse',button:2,pointerId:1});
  assert.equal(f.keys.size,0);
  f.btn('Space').dispatch('pointerdown',{pointerType:'touch',pointerId:2});
  f.btn('Space').dispatch('click',{detail:1});assert.equal(f.keys.size,1);
  f.btn('Space').dispatch('pointerup',{pointerId:2});f.tick(100);assert.equal(f.keys.size,0);
});
