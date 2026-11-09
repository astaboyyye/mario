"""Small authored mesh library; all scenery and characters are real geometry."""
import math
from functools import lru_cache
from panda3d.core import (Geom, GeomNode, GeomTriangles, GeomVertexData,
                         GeomVertexFormat, GeomVertexWriter, NodePath, Material)


@lru_cache(maxsize=3)
def mesh(shape):
    data = GeomVertexData(shape, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    v, n = GeomVertexWriter(data,'vertex'), GeomVertexWriter(data,'normal')
    triangles = GeomTriangles(Geom.UHStatic)
    if shape == 'box':
        faces = [((0,-1,0),[(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1)]),
                 ((0,1,0),[(1,1,-1),(-1,1,-1),(-1,1,1),(1,1,1)]),
                 ((1,0,0),[(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)]),
                 ((-1,0,0),[(-1,1,-1),(-1,-1,-1),(-1,-1,1),(-1,1,1)]),
                 ((0,0,1),[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]),
                 ((0,0,-1),[(-1,1,-1),(1,1,-1),(1,-1,-1),(-1,-1,-1)])]
        for normal, points in faces:
            base=v.getWriteRow()
            for point in points: v.addData3(*point); n.addData3(*normal)
            triangles.addVertices(base,base+1,base+2); triangles.addVertices(base,base+2,base+3)
    elif shape == 'star':
        points=[]
        for i in range(10):
            angle=math.pi/2+i*math.pi/5;r=1 if i%2==0 else .45
            points.append((math.cos(angle)*r,math.sin(angle)*r))
        for y,sign in ((-.3,-1),(.3,1)):
            for i in range(10):
                base=v.getWriteRow();a=points[i];b=points[(i+1)%10]
                for x,z in ((0,0),a,b):v.addData3(x,y,z);n.addData3(0,sign,0)
                triangles.addVertices(base,base+1,base+2) if sign<0 else triangles.addVertices(base,base+2,base+1)
        for i in range(10):
            a=points[i];b=points[(i+1)%10];base=v.getWriteRow()
            for x,y,z in ((a[0],-.3,a[1]),(a[0],.3,a[1]),(b[0],.3,b[1]),(b[0],-.3,b[1])):
                v.addData3(x,y,z);n.addData3(x,0,z)
            triangles.addVertices(base,base+1,base+2);triangles.addVertices(base,base+2,base+3)
    else:
        rows,cols=12,20
        for row in range(rows+1):
            theta=math.pi*row/rows
            for col in range(cols+1):
                phi=2*math.pi*col/cols
                point=(math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta))
                v.addData3(*point); n.addData3(*point)
        for row in range(rows):
            for col in range(cols):
                a=row*(cols+1)+col;b=a+cols+1
                triangles.addVertices(a,b,a+1);triangles.addVertices(a+1,b,b+1)
    geom=Geom(data);geom.addPrimitive(triangles)
    node=GeomNode(shape);node.addGeom(geom)
    return node


def part(parent, shape, pos, scale, color):
    node=parent.attachNewNode(mesh(shape).makeCopy())
    node.setPos(*pos);node.setScale(*scale);node.setColor(*color,1)
    material=Material();material.setShininess(18);material.setSpecular((.12,.12,.12,1))
    node.setMaterial(material)
    return node


def mario(parent):
    root=parent.attachNewNode('Mario')
    red=(.87,.09,.08);blue=(.07,.27,.68);skin=(1,.72,.48);brown=(.19,.08,.035)
    part(root,'sphere',(0,0,1.05),(.38,.27,.45),blue)
    part(root,'sphere',(0,0,1.34),(.43,.27,.25),red)
    part(root,'box',(-.23,-.27,1.27),(.07,.035,.21),blue)
    part(root,'box',(.23,-.27,1.27),(.07,.035,.21),blue)
    for x in (-.23,.23): part(root,'sphere',(x,-.31,1.15),(.055,.03,.055),(1,.78,.12))
    part(root,'sphere',(0,0,1.84),(.39,.32,.39),skin)
    part(root,'sphere',(0,.14,1.83),(.39,.28,.34),brown)
    part(root,'sphere',(0,-.33,1.83),(.16,.18,.15),skin)
    for x in (-.14,.14):
        part(root,'sphere',(x,-.29,1.96),(.08,.045,.12),(1,1,1))
        part(root,'sphere',(x,-.335,1.96),(.034,.018,.07),(.05,.2,.38))
        part(root,'sphere',(x,-.32,1.68),(.16,.06,.075),brown)
    part(root,'sphere',(0,0,2.12),(.43,.34,.2),red)
    part(root,'sphere',(0,-.31,2.09),(.42,.25,.045),red)
    part(root,'sphere',(0,-.31,2.2),(.12,.035,.1),(1,1,1))
    limbs=[]
    for x in (-.26,.26):
        leg=root.attachNewNode('leg');leg.setPos(x,0,.72)
        part(leg,'sphere',(0,0,-.19),(.18,.19,.3),blue)
        part(leg,'sphere',(0,-.11,-.52),(.23,.35,.17),brown);limbs.append(leg)
    for x in (-.5,.5):
        arm=root.attachNewNode('arm');arm.setPos(x,0,1.35)
        part(arm,'sphere',(0,0,-.15),(.16,.17,.3),red)
        part(arm,'sphere',(0,-.03,-.4),(.2,.2,.22),(1,.97,.88));limbs.append(arm)
    return root,limbs


def goomba(parent, guard=False):
    root=parent.attachNewNode('guard' if guard else 'Goomba')
    part(root,'sphere',(0,0,.62),(.6,.42,.5),(.52,.22,.09) if not guard else (.45,.14,.28))
    part(root,'sphere',(0,0,.29),(.34,.28,.28),(.97,.78,.51))
    for x in (-.25,.25):
        part(root,'sphere',(x,-.12,.13),(.27,.35,.13),(.2,.1,.055))
        part(root,'sphere',(x,-.39,.69),(.13,.05,.18),(1,1,.9))
        part(root,'sphere',(x,-.44,.67),(.045,.02,.09),(.1,.08,.07))
    if guard: part(root,'sphere',(0,0,1.1),(.55,.39,.13),(.95,.63,.11))
    return root


def bowser_jr(parent):
    root=parent.attachNewNode('Bowser Jr')
    part(root,'sphere',(0,.25,1.1),(.8,.45,.75),(.15,.46,.12))
    part(root,'sphere',(0,0,1.1),(.63,.44,.73),(.95,.63,.13))
    part(root,'sphere',(0,-.12,1.95),(.66,.46,.56),(.27,.62,.13))
    part(root,'sphere',(0,-.5,1.78),(.52,.34,.3),(1,.78,.35))
    for x in (-.27,.27):
        part(root,'sphere',(x,-.46,2.13),(.16,.07,.2),(1,1,.95))
        part(root,'sphere',(x,-.53,2.12),(.06,.02,.09),(.1,.1,.1))
        part(root,'sphere',(x,-.1,.28),(.31,.36,.25),(.9,.5,.08))
    for x in (-.3,0,.3): part(root,'sphere',(x,0,2.48),(.14,.18,.23),(.85,.1,.06))
    return root


def tree(parent,x,y,z=0):
    root=parent.attachNewNode('apple-tree');root.setPos(x,y,z)
    part(root,'box',(0,0,1.8),(.22,.22,1.8),(.42,.24,.13))
    for dx,dy,dz,size in ((0,0,4,1.6),(-.8,0,3.4,1.1),(.9,.2,3.6,1.2)):
        part(root,'sphere',(dx,dy,dz),(size,size*.8,size),(.21,.5,.2))
    for dx,dz in ((-.7,3.2),(.7,4.1),(.3,3)):
        part(root,'sphere',(dx,-1,dz),(.17,.17,.2),(.9,.13,.08))
    root.flattenStrong()
    return root
