"""Deterministic platform movement and campaign rules, independent of rendering."""
import math
from .campaign import STAGES


class Session:
    def __init__(self, index=0):
        self.index=index;self.stage=STAGES[index];self.time=0
        self.x=2.;self.z=0.;self.vx=0.;self.vz=0.
        self.grounded=True;self.coyote=.12;self.jump_buffer=0
        self.support=None;self.hp=3;self.invulnerable=0;self.cooldown=0
        self.burst=0;self.switches=set();self.medals=set();self.coins=set()
        self.checkpoint=False;self.completed=False;self.deaths=0
        self.message='';self.message_time=0;self.events=[]
        self.enemies=[{'x':(a+b)/2,'a':a,'b':b,'dir':1,'alive':True} for a,b in self.stage.enemies]
        self.boss_hp=3;self.boss_iframes=0;self.boss_x=77.;self.bullets=[]
        self.last_shot=0
        self.coin_positions=[]
        for a,b,h in self.stage.ground:
            for x in range(max(5,int(a)+3),int(b)-1,4): self.coin_positions.append((x,h+1.1))

    def platforms(self, time=None):
        t=self.time if time is None else time
        fixed=[(a,b,h,4) for a,b,h in self.stage.ground]+[(a,b,h,.45) for a,b,h in self.stage.platforms]
        for a,b,h,dx,dz,speed in self.stage.movers:
            offset=math.sin(t*speed)*dz
            fixed.append((a,b,h+offset,.45))
        return fixed

    def say(self, message):
        self.message=message;self.message_time=3

    def hurt(self):
        if self.invulnerable>0:return
        self.hp-=1;self.invulnerable=1.6;self.events.append('hurt')
        if self.hp<=0:self.respawn()

    def respawn(self):
        self.x=self.stage.checkpoint if self.checkpoint else 2
        self.z=max((h for a,b,h in self.stage.ground if a<=self.x<=b),default=0)+.1
        self.vx=self.vz=0;self.hp=3;self.invulnerable=2;self.support=None
        self.deaths+=1;self.bullets.clear();self.events.append('respawn')
        self.say('Back at the checkpoint. Your repairs and medals are safe.')

    def jump(self):self.jump_buffer=.15

    def interact(self):
        if self.stage.theme not in ('orchard','quarry'):return
        for i,(x,z) in enumerate(self.stage.switches):
            if i not in self.switches and abs(self.x-x)<2.6 and abs(self.z+1-z)<2.8:
                self.switches.add(i);self.events.append('repair')
                self.say('Water wheel opened.' if self.stage.theme=='orchard' else 'Lift brake released.')

    def power(self):
        if self.cooldown>0:return
        self.cooldown=2.6;self.burst=.35;self.events.append('power')
        for i,e in enumerate(self.enemies):
            ground=self.ground_height(e['x'])
            if e['alive'] and abs(e['x']-self.x)<3.8 and abs(ground-self.z)<2.5:self.kill_enemy(i)
        if self.stage.theme in ('foundry','citadel'):
            for i,(x,z) in enumerate(self.stage.switches):
                if abs(x-self.x)<3.8 and abs(z-self.z-1)<3:
                    self.switches.add(i);self.events.append('repair');self.say('Power restored.' if self.stage.theme=='foundry' else 'Steam valve vented.')
        if self.index==4 and abs(self.x-self.boss_x)<4.2:self.hit_boss()
        self.bullets=[b for b in self.bullets if abs(b[0]-self.x)>4]

    def hit_boss(self):
        if len(self.switches)<2:
            self.say('His steam shield is up. Vent both valves first.');return
        if self.boss_iframes>0 or self.boss_hp<=0:return
        self.boss_hp-=1;self.boss_iframes=1.8;self.events.append('stomp')
        if self.boss_hp==0:self.say('The engine is stopped! Reach the Power Star.')

    def kill_enemy(self,i):
        self.enemies[i]['alive']=False;self.events.append('stomp')
        if self.stage.theme=='train':self.switches.add(i);self.say('Conductor key recovered!')

    def ground_height(self,x):
        return max((h for a,b,h in self.stage.ground if a<=x<=b),default=-10)

    def step(self,dt,direction=0,run=False,held_jump=False):
        if self.completed:return
        old_time=self.time;self.time+=dt
        for name in ('invulnerable','cooldown','burst','message_time','boss_iframes','jump_buffer'):
            setattr(self,name,max(0,getattr(self,name)-dt))
        current=self.platforms();previous=self.platforms(old_time)
        if self.support is not None and self.grounded:self.z+=current[self.support][2]-previous[self.support][2]
        self.coyote=.12 if self.grounded else max(0,self.coyote-dt)
        speed=9.5 if run else 6.3
        target=direction*speed
        accel=40 if direction else 50
        self.vx+=max(-accel*dt,min(accel*dt,target-self.vx))
        if self.jump_buffer>0 and self.coyote>0:
            self.vz=14;self.grounded=False;self.coyote=0;self.jump_buffer=0;self.support=None;self.events.append('jump')
        if not held_jump and self.vz>6:self.vz-=40*dt
        old_x=self.x;old_z=self.z
        belt=0
        if self.stage.theme=='foundry' and self.grounded and (5<self.x<20 or 55<self.x<77):belt=2.2 if len(self.switches)==2 else -2.2
        self.x=max(-5,min(self.stage.exit+3,self.x+(self.vx+belt)*dt))
        for a,b,h,depth in current:
            if self.z<h-.12 and self.z+2>h-depth+.05 and self.x+.38>a and self.x-.38<b:
                if old_x+.38<=a:self.x=a-.38;self.vx=0
                elif old_x-.38>=b:self.x=b+.38;self.vx=0
        self.vz-=28*dt;self.z+=self.vz*dt;self.grounded=False;self.support=None
        for i,(a,b,h,depth) in enumerate(current):
            if self.x+.3>a and self.x-.3<b:
                old_h=previous[i][2]
                if self.vz<=0 and old_z>=old_h-.08 and self.z<=h:
                    self.z=h;self.vz=0;self.grounded=True;self.support=i
                elif self.vz>0 and old_z+2<=old_h-depth and self.z+2>=h-depth:
                    self.z=h-depth-2;self.vz=0
        if self.z<-8:self.respawn();return
        if not self.checkpoint and self.x>=self.stage.checkpoint:
            self.checkpoint=True;self.events.append('checkpoint');self.say('Checkpoint reached. Take your time; the train can wait.')
        for i,(x,z) in enumerate(self.stage.medals):
            if i not in self.medals and abs(self.x-x)<.8 and abs(self.z+1-z)<1:
                self.medals.add(i);self.events.append('medal')
        for i,(x,z) in enumerate(self.coin_positions):
            if i not in self.coins and abs(self.x-x)<.65 and abs(self.z+1-z)<1:
                self.coins.add(i);self.events.append('coin')
        for i,e in enumerate(self.enemies):
            if not e['alive']:continue
            e['x']+=e['dir']*1.5*dt
            if e['x']>e['b']:e['x']=e['b'];e['dir']=-1
            if e['x']<e['a']:e['x']=e['a'];e['dir']=1
            h=self.ground_height(e['x'])
            if abs(self.x-e['x'])<.75 and self.z<h+1 and self.z+2>h:
                if self.vz<0 and old_z>=h+.7:self.kill_enemy(i);self.vz=10
                else:self.hurt()
        if self.index==4 and self.boss_hp>0:
            self.boss_x=76+math.sin(self.time*.8)*5
            if self.x>60 and self.time-self.last_shot>2:
                self.bullets.append([self.boss_x,1.1,-7 if self.x<self.boss_x else 7]);self.last_shot=self.time
            if abs(self.x-self.boss_x)<1 and self.z<2.2:
                if self.vz<0 and old_z>1.8:self.hit_boss();self.vz=11
                else:self.hurt()
        for b in self.bullets:
            b[0]+=b[2]*dt
            if abs(self.x-b[0])<.6 and self.z<b[1]+.3 and self.z+2>b[1]-.3:self.hurt()
        self.bullets=[b for b in self.bullets if 55<b[0]<96]
        if self.x>=self.stage.exit-1:
            if len(self.switches)==2 and (self.index!=4 or self.boss_hp==0):
                self.completed=True;self.events.append('clear')
            else:
                self.x=self.stage.exit-1.1;self.say('Finish the repair first.' if self.index!=4 else 'Stop Jr. before taking the Power Star.')
