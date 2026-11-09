"""The Last Train to Starfall: 3D rendering, input, and campaign presentation."""
import json
import math
import sys
from pathlib import Path
from panda3d.core import (AmbientLight, DirectionalLight, Vec4, Vec3, OrthographicLens,
                         WindowProperties, TextNode, Filename, loadPrcFileData, AntialiasAttrib,
                         VirtualFileSystem, VirtualFileMountRamdisk, PNMImage, StringStream, ClockObject)
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton
from .models import part, mario, goomba, bowser_jr, tree
from .simulation import Session
from .campaign import STAGES

ROOT=Path(__file__).resolve().parent.parent
SAVE=(Path(sys.executable).parent if getattr(sys,'frozen',False) else ROOT)/'starfall-save.json'
INK=(.055,.085,.13,1); PAPER=(1,.96,.86,1); GOLD=(1,.74,.19,1)
PALETTES={
    'orchard':((.51,.78,.85),(.3,.58,.23),(.46,.31,.18)),
    'quarry':((.62,.74,.82),(.53,.59,.48),(.39,.43,.43)),
    'foundry':((.23,.29,.39),(.55,.37,.22),(.25,.28,.32)),
    'train':((.64,.76,.88),(.56,.24,.21),(.24,.29,.36)),
    'citadel':((.22,.22,.36),(.42,.36,.48),(.24,.23,.32)),
}


class Game(ShowBase):
    def __init__(self, smoke=False):
        loadPrcFileData('', 'window-title Mario: The Last Train to Starfall\nwin-size 1280 720\nsync-video true\nshow-frame-rate-meter false\nframebuffer-multisample 1\nmultisamples 4\naudio-library-name p3openal\nnotify-level warning')
        if smoke:loadPrcFileData('', 'window-type offscreen\naudio-library-name null')
        loadPrcFileData('', 'model-cache-models false\nmodel-cache-textures false')
        # Mount bytes explicitly: supports bundled resources and restricted folders
        # without requiring the engine to enumerate their parent directories.
        vfs=VirtualFileSystem.getGlobalPtr()
        vfs.mount(VirtualFileMountRamdisk(), '/game-assets', 0)
        for path in (ROOT/'resources').rglob('*'):
            if path.suffix.lower() in ('.ttf','.ogg','.wav'):
                name='/game-assets/'+path.relative_to(ROOT/'resources').as_posix()
                vfs.makeDirectoryFull(Filename(name).getDirname())
                vfs.writeFile(name,path.read_bytes(),False)
        super().__init__()
        self.ui_font=self.loader.loadFont('/game-assets/fonts/Nunito.ttf')
        self.disableMouse();self.render.setAntialias(AntialiasAttrib.MAuto)
        self.smoke=smoke;self.keys=set();self.state='title';self.muted=False;self.fullscreen=False
        self.progress={'unlocked':0,'medals':{}}
        if not smoke:
            try:
                raw=json.loads(SAVE.read_text());self.progress={'unlocked':max(0,min(4,int(raw.get('unlocked',0)))),'medals':raw.get('medals',{})}
            except (OSError,ValueError,TypeError):pass
        self.cam_x=4.;self.accumulator=0;self.effects=[];self.overlay=None
        self.lens=OrthographicLens();self.lens.setFilmSize(32,18);self.lens.setNearFar(.1,250)
        self.cam.node().setLens(self.lens)
        ambient=AmbientLight('sky-light');ambient.setColor((.57,.61,.68,1));self.render.setLight(self.render.attachNewNode(ambient))
        sun=DirectionalLight('sun');sun.setColor((1,.9,.73,1));sun.setShadowCaster(True,2048,2048)
        sun.getLens().setFilmSize(45,35);sun.getLens().setNearFar(1,90)
        self.sun=self.render.attachNewNode(sun);self.sun.setHpr(-25,-55,0);self.render.setLight(self.sun)
        self.render.setShaderAuto()
        self.world=None;self.sounds={};self.music=None
        for event,file in {'jump':'small_jump.ogg','coin':'coin.ogg','medal':'powerup.ogg','repair':'powerup.ogg','stomp':'stomp.ogg','hurt':'bump.ogg','power':'fireball.ogg','checkpoint':'one_up.ogg','clear':'one_up.ogg'}.items():
            sound=self.loader.loadSfx('/game-assets/sound/'+file)
            if sound:sound.setVolume(.35);self.sounds[event]=sound
        self.music=self.loader.loadMusic('/game-assets/music/main_theme.ogg')
        if self.music:self.music.setLoop(True);self.music.setVolume(.16)
        for key in ('arrow_left','arrow_right','a','d','shift','space'):
            self.accept(key,self.key,[key,True]);self.accept(key+'-up',self.key,[key,False])
        self.accept('z',self.action);self.accept('e',self.interact)
        self.accept('enter',self.confirm);self.accept('escape',self.pause);self.accept('p',self.pause)
        self.accept('r',self.retry);self.accept('m',self.mute);self.accept('f11',self.toggle_fullscreen)
        if not smoke:self.accept('window-event',self.window_event)
        self.make_hud();self.load_stage(0,brief=False);self.title()
        self.taskMgr.add(self.tick,'game')

    def label(self,parent,text,x,z,size=.045,color=PAPER,align=TextNode.ALeft):
        return DirectLabel(parent=parent,text=text,text_align=align,text_fg=color,text_scale=size,
                           frameColor=(0,0,0,0),pos=(x,0,z),text_font=self.ui_font)

    def button(self,parent,text,x,z,command,width=1.3):
        return DirectButton(parent=parent,text=text,text_scale=.047,text_font=self.ui_font,text_fg=INK,frameColor=GOLD,
                            frameSize=(-width/2,width/2,-.06,.08),pos=(x,0,z),command=command,
                            relief=1,rolloverSound=None,clickSound=None)

    def make_hud(self):
        self.hud=DirectFrame(frameColor=INK,frameSize=(-1.72,1.72,-.08,.09),pos=(0,0,.86))
        self.hud_name=self.label(self.hud,'',-1.64,.035,.04,GOLD)
        self.hud_objective=self.label(self.hud,'',-1.64,-.035,.032)
        self.hud_stats=self.label(self.hud,'',1.62,.005,.042,align=TextNode.ARight)
        self.bottom=DirectFrame(frameColor=(.04,.06,.1,.84),frameSize=(-1.72,1.72,-.035,.055),pos=(0,0,-.91))
        self.hint=self.label(self.bottom,'',0,0,.032,align=TextNode.ACenter)
        self.notice=self.label(self.aspect2d,'',0,-.72,.045,GOLD,TextNode.ACenter)

    def clear_overlay(self):
        if self.overlay:self.overlay.destroy();self.overlay=None

    def modal(self):
        self.clear_overlay()
        self.overlay=DirectFrame(frameColor=(.035,.055,.09,.96),frameSize=(-1.35,1.35,-.72,.72))
        return self.overlay

    def title(self):
        if self.session.index != 0:self.load_stage(0,brief=False)
        self.session.x=15;self.session.z=0
        self.state='title';self.hud.hide();self.bottom.hide();self.notice['text']=''
        self.clear_overlay()
        self.overlay=DirectFrame(frameColor=(.035,.055,.09,.95),frameSize=(-1.02,1.02,-.82,.82),pos=(-.63,0,.02))
        p=self.overlay
        self.label(p,'A MARIO FAN ADVENTURE',-.88,.65,.035,GOLD)
        self.label(p,'The Last Train',-.89,.39,.105)
        self.label(p,'to Starfall',-.89,.26,.105)
        self.label(p,'Five stops. One stolen train.',-.88,.08,.045,GOLD)
        self.label(p,'Repair the railway, catch Bowser Jr.,\nand get everyone to the festival.',-.88,-.07,.044)
        self.button(p,'CONTINUE' if self.progress['unlocked'] else 'BEGIN THE JOURNEY',0,-.34,self.start_saved,1.74)
        self.button(p,'CHOOSE A STOP',0,-.53,self.route,1.74)
        self.label(p,'SPACE jump    Z star burst    E interact',-.88,-.72,.031)
        self.sync_visuals(1)

    def start_saved(self):self.load_stage(self.progress['unlocked'])

    def route(self):
        self.state='route';p=self.modal()
        self.label(p,'THE STARFALL LINE',-1.15,.54,.065,GOLD)
        for i,stage in enumerate(STAGES):
            unlocked=i<=self.progress['unlocked']
            medals=self.progress['medals'].get(str(i),0)
            title=f'{i+1}.  {stage.name}    {medals}/3 medals' if unlocked else f'{i+1}.  Next stop locked'
            self.button(p,title,0,.29-i*.17,lambda n=i: self.load_stage(n) if n<=self.progress['unlocked'] else None,2.3)
        self.label(p,'ESC returns to the title screen',-1.15,-.64,.031)

    def briefing(self):
        self.state='brief';p=self.modal();s=self.session.stage
        self.label(p,s.place,-1.15,.53,.04,GOLD)
        self.label(p,s.name,-1.15,.34,.08)
        self.label(p,s.speaker,-1.15,.17,.035,GOLD)
        label=self.label(p,self.wrap(s.briefing,64),-1.15,.04,.043)
        self.label(p,s.objective,-1.15,-.32,.038,GOLD)
        self.button(p,'ENTER  /  LET\'S GO',0,-.53,self.play,1.8)

    @staticmethod
    def wrap(text,width=64):
        import textwrap
        return '\n'.join(textwrap.wrap(text,width))

    def play(self):
        self.clear_overlay();self.state='play';self.keys.clear();self.hud.show();self.bottom.show()
        if self.music and not self.muted:self.music.play()

    def finish(self):
        self.state='clear';self.progress['unlocked']=min(4,max(self.progress['unlocked'],self.session.index+1))
        key=str(self.session.index);self.progress['medals'][key]=max(self.progress['medals'].get(key,0),len(self.session.medals))
        if not self.smoke:
            try:SAVE.write_text(json.dumps(self.progress,indent=2))
            except OSError:self.session.say('Progress could not be saved. Check folder permissions.')
        p=self.modal();final=self.session.index==4
        self.label(p,'NEXT STOP: THE FESTIVAL' if final else 'TRACK CLEAR',-1.15,.51,.06,GOLD)
        self.label(p,self.wrap(self.session.stage.ending,65),-1.15,.27,.043)
        self.label(p,f'{len(self.session.medals)}/3 medals   /   {len(self.session.coins)} coins   /   {self.session.deaths} retries',-1.15,-.16,.04,GOLD)
        self.button(p,'BACK TO THE ROUTE' if final else 'ENTER  /  NEXT STOP',0,-.49,self.next_stage,2)

    def next_stage(self):
        if self.session.index==4:self.route()
        else:self.load_stage(self.session.index+1)

    def load_stage(self,index,brief=True):
        if self.world:self.world.removeNode()
        self.world=self.render.attachNewNode('stage');self.session=Session(index);self.effects=[]
        s=self.session.stage;sky,turf,soil=PALETTES[s.theme];self.setBackgroundColor(*sky)
        self.static=self.world.attachNewNode('scenery')
        self.backdrop=self.world.attachNewNode('distant-landscape')
        for a,b,h in s.ground:
            part(self.static,'box',((a+b)/2,0,h-2),((b-a)/2,2.6,2),soil)
            part(self.static,'box',((a+b)/2,0,h-.1),((b-a)/2,2.66,.12),turf)
            if s.theme=='train':
                for x in (a+2,b-2):
                    part(self.static,'sphere',(x,-2.55,h-1.7),(.7,.18,.7),(.09,.12,.17))
                part(self.static,'box',((a+b)/2,1.9,h+.45),((b-a)/2,.12,.45),(.75,.48,.17))
        for a,b,h in s.platforms:
            part(self.static,'box',((a+b)/2,0,h-.25),((b-a)/2,1.65,.25),(.62,.38,.17) if s.theme=='orchard' else turf)
            part(self.static,'box',((a+b)/2,-1.66,h-.18),((b-a)/2,.06,.07),(.95,.73,.32))
        self.mover_nodes=[]
        for a,b,h,dx,dz,speed in s.movers:
            node=self.world.attachNewNode('lift');self.mover_nodes.append(node)
            part(node,'box',(0,0,-.25),((b-a)/2,1.7,.25),(.86,.62,.22))
            for x in (a,b):part(self.static,'box',(x,1.8,2),(.08,.08,5),(.3,.34,.38))
        # Dioramas use a consistent palette and repeat structural details, not random props.
        for x in range(-10,110,9):
            if s.theme=='orchard':tree(self.static,x,5)
            elif s.theme=='quarry':
                part(self.static,'sphere',(x,9,2),(5,4,6),(.43,.49,.51))
                part(self.static,'box',(x,5,1.4),(1.3,1.3,1.4),(.46,.3,.17))
            elif s.theme in ('foundry','citadel'):
                part(self.static,'box',(x,8,5),(2.7,2,7),(.24,.27,.32) if s.theme=='foundry' else (.3,.27,.4))
                for z in (2,5,8):part(self.static,'box',(x,5.95,z),(.48,.05,.75),(1,.55,.16))
            else:
                part(self.static,'sphere',(x,18,-2),(7,5,5),(.66,.72,.8))
        for x in range(-20,130,17):
            part(self.backdrop,'sphere',(x,28,-9),(11,5,7),(.3,.5,.48) if s.theme=='orchard' else (.39,.43,.55))
            for dx,z,sc in ((0,11,2),(2,11.5,2.5),(4,11,1.7)):
                part(self.backdrop,'sphere',(x+dx,12,z-4),(sc,1,sc*.5),(.95,.95,.88))
        if s.theme=='orchard':
            part(self.static,'box',(42,4,-.05),(50,.6,.05),(.18,.58,.72))
            for x in (20,72):part(self.static,'box',(x,3.7,1),(.25,.3,1),(.5,.29,.12))
        if s.theme=='foundry':
            for a,b in ((5,20),(55,77)):
                for x in range(a,b):part(self.static,'box',(x,0,.04),(.25,2.3,.05),(.85,.63,.2))
        if s.theme=='citadel':
            # The stolen engine sits behind the arena, leaving the fight readable.
            part(self.static,'sphere',(76,4,2.5),(5,1.5,1.6),(.17,.24,.27))
            for x in (73,76,79):part(self.static,'sphere',(x,4,2.5),(.12,1.55,1.65),(.75,.52,.21))
            part(self.static,'box',(72,4,4.8),(.6,.6,1.5),(.13,.17,.19))
            part(self.static,'box',(81,4,3),(1.5,1.5,2.5),(.55,.16,.12))
            part(self.static,'box',(80.5,2.48,3.8),(.7,.04,.7),(.88,.76,.43))
            for x in (72,75,78,81):part(self.static,'sphere',(x,2.6,.8),(.85,.2,.85),(.12,.14,.17))
        # Checkpoint and destination are readable from the play lane.
        self.checkflag=part(self.static,'box',(s.checkpoint,1.6,2),(.06,.06,2),(.85,.83,.73))
        self.flagcloth=part(self.world,'box',(s.checkpoint+.45,1.6,3.5),(.45,.07,.3),(.8,.2,.15))
        part(self.static,'box',(s.exit,2,2),(.12,.12,2),(.86,.8,.64))
        part(self.static,'box',(s.exit,2,3.5),(1.4,.15,.5),(.15,.25,.28))
        self.exit_star=part(self.world,'star',(s.exit,0,2.3),(.6,.3,.6),(1,.78,.12))
        self.switch_nodes=[]
        for i,(x,z) in enumerate(s.switches):
            node=self.world.attachNewNode('repair');node.setPos(x,0,z)
            part(node,'box',(0,.3,-.45),(.45,.35,.5),(.26,.35,.38))
            part(node,'sphere',(0,-.1,0),(.55,.12,.55),(.91,.4,.12))
            part(node,'box',(0,-.25,0),(.08,.08,.46),(.95,.8,.42))
            self.switch_nodes.append(node)
        self.enemy_nodes=[goomba(self.world,s.theme=='train') for _ in self.session.enemies]
        if s.theme=='train':
            for n in self.switch_nodes:n.hide()
        self.medal_nodes=[part(self.world,'sphere',(x,0,z),(.32,.13,.42),(1,.63,.16)) for x,z in s.medals]
        self.coin_nodes=[part(self.world,'sphere',(x,0,z),(.18,.06,.24),(1,.85,.2)) for x,z in self.session.coin_positions]
        self.hero,self.limbs=mario(self.world)
        self.shadow=part(self.world,'sphere',(2,0,.02),(.7,.45,.015),(.12,.18,.17))
        self.boss=bowser_jr(self.world) if index==4 else None
        self.bullet_nodes=[]
        self.static.flattenStrong()
        self.backdrop.flattenStrong()
        self.cam_x=4.;self.accumulator=0;self.sync_visuals(0)
        if brief:self.briefing()

    def key(self,key,down):
        if down:self.keys.add(key)
        else:self.keys.discard(key)
        if key=='space' and down and self.state=='play':self.session.jump()

    def action(self):
        if self.state=='play':self.session.power()

    def interact(self):
        if self.state=='play':self.session.interact()

    def confirm(self):
        if self.state=='title':self.start_saved()
        elif self.state=='brief':self.play()
        elif self.state=='clear':self.next_stage()
        elif self.state=='pause':self.play()

    def pause(self):
        if self.state=='play':
            self.state='pause';self.keys.clear();p=self.modal()
            self.label(p,'Take a breather.',-1.15,.42,.08)
            self.button(p,'RESUME',0,.1,self.play)
            self.button(p,'ROUTE MAP',0,-.13,self.route)
            self.button(p,'QUIT',0,-.36,self.userExit)
        elif self.state=='pause':self.play()
        elif self.state in ('route','brief'):self.title()

    def retry(self):
        if self.state=='play':self.session.respawn()

    def mute(self):
        self.muted=not self.muted
        if self.music:self.music.setVolume(0 if self.muted else .16)

    def toggle_fullscreen(self):
        if self.smoke:return
        self.fullscreen=not self.fullscreen;p=WindowProperties();p.setFullscreen(self.fullscreen)
        if not self.fullscreen:p.setSize(1280,720)
        self.win.requestProperties(p)

    def window_event(self,window):
        if window and not window.getProperties().getForeground() and self.state=='play':self.pause()

    def sync_visuals(self,dt):
        s=self.session;t=s.time
        if s.stage.theme=='train':self.backdrop.setX(-(t*5)%17)
        self.hero.setPos(s.x,0,s.z)
        facing=-20 if s.vx>0 else 20 if s.vx<0 else 0
        self.hero.setH(facing)
        for i,limb in enumerate(self.limbs):limb.setP(math.sin(t*13+i%2*math.pi)*min(32,abs(s.vx)*5) if s.grounded else (-30 if i<2 else 35))
        self.hero.setColorScale(1,1,1,.45 if s.invulnerable>0 and int(t*12)%2 else 1)
        h=s.ground_height(s.x);self.shadow.setPos(s.x,0,max(-6,h)+.025)
        for i,node in enumerate(self.mover_nodes):
            a,b,h,depth=s.platforms()[len(s.stage.ground)+len(s.stage.platforms)+i];node.setPos((a+b)/2,0,h)
        for i,node in enumerate(self.enemy_nodes):
            e=s.enemies[i]
            if not e['alive']:node.hide()
            else:node.setPos(e['x'],0,s.ground_height(e['x'])+abs(math.sin(t*7+i))*.06)
        for i,node in enumerate(self.switch_nodes):
            if i in s.switches:node.setColorScale(.3,1,.45,1)
        for nodes,positions,collected in ((self.medal_nodes,s.stage.medals,s.medals),(self.coin_nodes,s.coin_positions,s.coins)):
            for i,node in enumerate(nodes):
                if i in collected:node.hide()
                else:node.setH(t*100);node.setZ(positions[i][1]+math.sin(t*2+i)*.12)
        if s.checkpoint:self.flagcloth.setColor(.2,.8,.5,1)
        self.exit_star.setH(t*75)
        if self.boss:
            self.boss.setPos(s.boss_x,0,0)
            if s.boss_hp<=0:self.boss.hide()
            else:self.boss.setColorScale(1,.5 if s.boss_iframes>0 else 1,.5 if s.boss_iframes>0 else 1,1)
        while len(self.bullet_nodes)<len(s.bullets):self.bullet_nodes.append(part(self.world,'sphere',(0,0,0),(.3,.3,.3),(1,.25,.04)))
        for i,node in enumerate(self.bullet_nodes):
            if i<len(s.bullets):node.show();node.setPos(s.bullets[i][0],0,s.bullets[i][1])
            else:node.hide()
        for node,life in self.effects[:]:
            life-=dt
            if life<=0:node.removeNode();self.effects.remove(next(e for e in self.effects if e[0]==node))
            else:node.setScale(1+(1-life/.35)*4);self.effects[self.effects.index(next(e for e in self.effects if e[0]==node))]=(node,life)
        target=s.x+3 if self.state not in ('title','route') else 6
        self.cam_x+=(target-self.cam_x)*min(1,dt*5)
        self.camera.setPos(self.cam_x,-30,15);self.camera.lookAt(self.cam_x,0,3)
        self.sun.setPos(self.cam_x-10,-15,30)
        self.hud_name['text']=s.stage.place+'   /   '+s.stage.name
        self.hud_objective['text']=s.stage.objective
        boss=f'   JR {s.boss_hp}/3' if s.index==4 else ''
        objective='keys' if s.stage.theme=='train' else 'valves' if s.index==4 else 'repairs'
        self.hud_stats['text']=f'HP {s.hp}   |   {len(s.switches)}/2 {objective}   |   {len(s.medals)}/3 medals'+boss
        power='Z burst READY' if s.cooldown<=0 else f'Z burst {s.cooldown:.1f}s'
        self.hint['text']=f'ARROWS / A D move     SPACE jump     SHIFT run     {power}     E interact     P pause     {len(s.coins)} coins'
        self.notice['text']=s.message if s.message_time>0 and self.state=='play' else ''

    def tick(self,task):
        dt=min(.1,globalClock.getDt())
        if self.state=='play':
            self.accumulator+=dt
            while self.accumulator>=1/120:
                direction=int('arrow_right' in self.keys or 'd' in self.keys)-int('arrow_left' in self.keys or 'a' in self.keys)
                self.session.step(1/120,direction,'shift' in self.keys,'space' in self.keys)
                self.accumulator-=1/120
            for event in self.session.events:
                if not self.muted and event in self.sounds:self.sounds[event].play()
                if event=='power':
                    ring=part(self.world,'sphere',(self.session.x,0,self.session.z+1),(.5,.5,.5),(1,.8,.25))
                    ring.setRenderModeWireframe();ring.setLightOff();self.effects.append((ring,.35))
            self.session.events.clear()
            if self.session.completed:self.finish()
        self.sync_visuals(dt)
        return task.cont


def main():
    smoke='--smoke-test' in sys.argv
    app=Game(smoke)
    if smoke:
        out=Path(sys.argv[sys.argv.index('--output')+1]) if '--output' in sys.argv else ROOT/'previews'
        out.mkdir(parents=True,exist_ok=True)
        clock=ClockObject.getGlobalClock();clock.setMode(ClockObject.MNonRealTime);clock.setDt(1/60)
        for i in range(5):
            app.load_stage(i,brief=False);app.play()
            for frame in range(120):
                if frame==10:app.key('space',True)
                if frame==30:app.action()
                if frame==50:app.key('space',False)
                app.taskMgr.step()
            app.session.x=5;app.session.z=0;app.sync_visuals(1)
            for _ in range(4):app.graphicsEngine.renderFrame()
            capture(app,out/f'stage-{i+1}.png')
        app.title()
        for _ in range(3):app.graphicsEngine.renderFrame()
        capture(app,out/'title.png')
        (out/'smoke-report.json').write_text(json.dumps({'stages_rendered':5,'simulation_frames':600,'result':'passed'}))
        app.destroy()
    else:app.run()


def capture(app,path):
    image=PNMImage();app.win.getScreenshot(image)
    stream=StringStream();image.write(stream,'preview.png')
    path.write_bytes(stream.getData())
