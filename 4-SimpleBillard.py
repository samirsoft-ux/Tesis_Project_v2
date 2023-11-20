import numpy as np
import cv2
import json
from math import *
import math
from time import *
import time
import matplotlib.pyplot as plt
import pymunk
import numpy.polynomial.polynomial as poly
from random import random
import os.path
############### Setting Importation ###############
with open('camera.json', 'r') as f:
    data = json.load(f)
for k,v in data.items():
    globals()[k]=v
print("Camera Data:", data)
with open('data.json', 'r') as f:
    data = json.load(f)
for k,v in data.items():
    globals()[k]=np.array(v)
print("Calibraton Data:", data)
############### Configuration Fenetre ###############
cv2.namedWindow("Billard", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Billard", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL) #, cv2.WINDOW_NORMAL, cv2.WINDOW_NORMAL) #
if os.path.isfile('debug.mp4'):
    cap = cv2.VideoCapture('debug.mp4')
else:
    cap = cv2.VideoCapture(camera_number)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 15)
    fps = int(cap.get(5))
    print("fps:", fps)
############### Billard ###############
ret, frame = cap.read()
l, h ,c = frame.shape
cadre = (1920, 1080)
print(l,h)
##### Moteur Physique #####
space = pymunk.Space()
space.gravity = (0, 0)
# Edge of billard:
body = space.static_body
body.position = (0, 0)
lEdges = [pymunk.Segment(body, (0, 0), (cadre[0], 0), 10),
          pymunk.Segment(body, (cadre[0], 0), (cadre[0], cadre[1]), 1),
          pymunk.Segment(body, (cadre[0], cadre[1]), (0, cadre[1]), 1),
          pymunk.Segment(body, (0, cadre[1]), (0, 0), 1)
]
for edge in lEdges:
    edge.elasticity = 0.95
    edge.friction = 0 ## 0.1
space.add(*lEdges)
class Ball:
    scoreLimit = 0.90
    pointLimit = 15 # points
    lBall=[]
    id_count=0
    radius = 27
    mass = 111
    deceleration = 26
    memory = 10 # Le nombre de point utiliser pour les calcules
    max_ball = 20
    sId_available = set(range(max_ball))
    def __init__(self, t, x, y):
        global space, t_physic_engine
        Ball.lBall+=[self]
        self.lPos = [[t, x, y]]
        self.lPos_prediction = [[t_physic_engine, x, y]]
        self.lVitesse = [[t, 0, 0, 0]]  # [[t, dx, dy, v]]
        self.lVitesse_prediction = [[t_physic_engine, 0, 0, 0]]
        self.polynome_distance = poly.Polynomial([0])
        self.debut_simulation = 0
        self.lChemin = []
        self.lVt1 = []
        self.lVt2 = []
        self.lTest = []
        self.lAngle = []
        self.lAcc = [[t, 0]]
        self.distance=0
        self.std = []
        self.id = min(Ball.sId_available)
        Ball.sId_available.remove(self.id)
        self.explosion_frame = 0
        self.debut_simulation = time.time()
        self.movement = 4
        self.prediction_run = False
        inertia = pymunk.moment_for_circle(Ball.mass, 0, Ball.radius, (0, 0))
        body = pymunk.Body(Ball.mass, inertia)
        body.position = (x, y)
        shape = pymunk.Circle(body, Ball.radius, (0, 0))
        shape.elasticity = 1 #0.95
        shape.friction = 0.1 #0.9
        space.add(body, shape)        
        body.velocity_func = self.static_friction
        self.shape = shape
        self.body = body
        self.creation_time = time.time()
    def static_friction(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, gravity, damping, dt)
        if self.prediction_run:
            if round(body.velocity.length,3) < 0.01:
                body.velocity = body.velocity*0
            else:
                if len(ball.lVitesse)>1:
                    v=float(self.lVitesse[-1][3])
                else:
                    v=0.0
                body.velocity = body.velocity/body.velocity.length * v * 2 * float(np.exp(-self.debut_simulation/4))
        else:
            pass
        self.debut_simulation += dt
    def remove_from_space(self):
        global space
        Ball.sId_available.add(self.id)
        if self.body in space.bodies:
            space.remove(self.body, self.shape)
        Ball.lBall.remove(self)
        del self
    def interpolation(self, dt):
        tv, dx, dy, v = self.lVitesse[-1]
        t, x, y = self.lPos[-1]
        dp = self.polynome_distance(tv) - self.polynome_distance(tv+dt)
        px = x + dx*v*dt
        py = y + dy*v*dt
        px = min(max(px, 1), 1919)
        py = min(max(py, 1), 1079)
        if v<15:
            v=0
            dx=0
            dy=0
        vx = dx*v
        vy = dy*v
        return px, py, vx, vy, v
    def add_pos(self, t, x, y):
        global space, t_physic_engine
        if len(self.lPos)>=1:
            _, x1, y1 = self.lPos[-1]
            d = ((x1 - x)**2 + (y1 - y)**2)**0.5
            if d<10:
                _, x, y = self.lPos[-1]
        # Limite le nombre de donné pour notre prédiction
        aAverage = np.array(self.lPos[-Ball.memory+1:] + [[t, x, y]])
        self.lPos += [list(np.average(aAverage,
                                      weights=np.exp((aAverage[:,0]-t)/0.1),
                                      axis=0))] # [[t, x, y], ...]
        if self.lPos_prediction[-1][0]!=t_physic_engine:
            self.lPos_prediction+=[[t_physic_engine] + list(self.body.position)]
            self.lVitesse_prediction+=[[t_physic_engine] + list(self.body.velocity) + [self.body.velocity.length]]
        if len(self.lPos) < ball.memory:
            return
        a = np.array(self.lPos[-2:])
        dt, dx, dy = a[1] - a[0]
        vx, vy = dx/dt, dy/dt
        self.lTest += [[t, (vx**2 + vy**2)**0.5]]
        lFitting_pos = self.lPos[-Ball.memory:]
        aFitting_pos = np.array(lFitting_pos)
        [[dx],[dy],[cx],[cy]] = cv2.fitLine(np.array([[[x,y]] for t,x,y in lFitting_pos]), cv2.DIST_L2, 0, 0.01, 0.01)
        # Déduit le sens:
        p0 = np.array(lFitting_pos[-2][1:3])
        p1 = np.array([cx+10*dx, cy+10*dy])
        p2 = np.array([cx-10*dx, cy-10*dy])
        d1 = np.linalg.norm(p0-p1)
        d2 = np.linalg.norm(p0-p2)
        if d2<d1:
            dx *= -1
            dy *= -1
        # Projection sur l'axe de la direction:
        aFitting_pos = np.array(lFitting_pos)
        lT = aFitting_pos[:,0]
        lXY = aFitting_pos[:,1:3]
        rotation_matrix = np.array([[dx , -dy], [dy, dx]]).T
        lDistance = rotation_matrix.dot(lXY.T)[0,:]
        t_mean = (lT[-1] + lT[0])/2
        # Interpolation polynomiale de l'avancement:
        coefs = poly.polyfit(lT, lDistance, 2)
        pd = poly.Polynomial(coefs)
        pv = pd.deriv()
        pa = pv.deriv()
        self.polynome_distance = pd
        v = pv(t_mean)
        acc = pa(t_mean)
        # Limiter les vitesses trop petite:
        if v<15:
            vx, vy, v = 0, 0, 0
        # Limiter les vitesses trop petite:
        if abs(acc)<1:
            acc = 0
        self.lAngle += [[t, np.arctan2(dx, dy)]]
        aAverage = np.array(self.lVitesse[-Ball.memory+1:] + [[t_mean, dx, dy, v]])
        self.lVitesse += [list(np.average(aAverage,
                                          weights=np.exp((aAverage[:,0]-t)/0.03),
                                          axis=0))] # [[t, vx, vy, v], ...]
        aAverage = np.array(self.lAcc[-Ball.memory+1:] + [[t_mean, acc]])
        self.lAcc += [list(np.average(aAverage,
                                      weights=np.exp((aAverage[:,0]-t)/1000),
                                      axis=0))] # [[t, acc], ...]
        _, px, py = self.lPos[-(Ball.memory+1)//2]
        self.lChemin += [[px,py]]
        pv = self.lVitesse[-1][3]
        sV=11
        self.lVt1 += [[px-dy*pv/sV, py+dx*pv/sV]]
        self.lVt2 += [[px+dy*pv/sV, py-dx*pv/sV]]
        if v>20:
            if not self.prediction_run:
                print("Launch",t,self.prediction_run,"id", self.id)
                dt = (time.time() - t_prediction)*7
                px = min(max(x + dx*v*dt, 1), 1919)
                py = min(max(y + dy*v*dt, 1), 1079)
                self.body.position = pymunk.Vec2d(px, py)
                self.body.velocity = pymunk.Vec2d(dx, dy) * 1000
                scale = 100
                #self.body.apply_impulse_at_local_point((dx*scale, dy*scale))
                self.prediction_run = True
                self.debut_simulation = 0
        if v==0:
            self.body.position = pymunk.Vec2d(x, y)
            self.body.velocity = pymunk.Vec2d(0, 0)
            self.prediction_run = False
            self.lPos_prediction = [[t_physic_engine, x, y]]
            self.lChemin = []
            self.lVt1 = []
            self.lVt2 = []
    @classmethod
    def mapping_detecting_balls(cls, t, lDetected_ball):
        if not lDetected_ball:
            return
        for ball in Ball.lBall:
            if t - ball.lPos[-1][0] > 1.5:
                ball.remove_from_space()
        lDistance = []
        lMapped_ball = set()
        lMapped_detected_ball = set()
        for ball in Ball.lBall:
            _, x1, y1 = ball.lPos[-1]
            for (x2, y2) in lDetected_ball:
                #assert not ((x2-x1)**2 + (y2-y1)**2)**0.5 in dDistance, "BUG !!!!!!!"
                lDistance += [[((x2-x1)**2 + (y2-y1)**2)**0.5, (x2, y2), ball]]
        lDistance = sorted(lDistance, key = lambda x: x[0])
        i = 0
        for d, detected, ball in lDistance:
            if i >= len(Ball.lBall):
                break
            if (not detected in lMapped_detected_ball) and (not ball in lMapped_ball):
                lMapped_detected_ball.add(detected)
                lMapped_ball.add(ball)
                lDetected_ball.remove(detected)
                ball.add_pos(t, *detected)
                i += 1  
        for detected in lDetected_ball:
            Ball(t, *detected)

_, frame = cap.read()
prevframe = frame[:,:,:] #frame[:,:,2]    #First frame
prevframe = cv2.warpPerspective(prevframe, m_camera2screen, (1920,1080), flags=cv2.INTER_LINEAR)
cv2.imshow('Billard', prevframe)
background = cv2.imread("background.jpg")[:,:,2]
background = cv2.warpPerspective(background, m_camera2screen, (1920,1080), flags=cv2.INTER_LINEAR)
fond = cv2.imread("FondDVIC.png")
debut_time = time.time()
n_frame = 0
first = True
t_prediction = time.time()
t_physic_engine = 0
##-->MIPARTE
def crear_bola(space, position, mass=1, radius=27):
    inertia = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, inertia)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.95  # coeficiente de restitución
    shape.friction = 0.9  # fricción de la bola
    space.add(body, shape)
    return body
def aplicar_impulso(bola, impulso):
    bola.apply_impulse_at_local_point(impulso)
def simular_movimientos_y_obtener_trayectorias(space, bolas_pymunk, steps=100):
    trayectorias = {bola: [] for bola in bolas_pymunk}
    for _ in range(steps):
        space.step(1/50.0)
        for bola in bolas_pymunk:
            trayectorias[bola].append(bola.position)
    return trayectorias
def dibujar_trayectorias(trayectorias, newframe):
    for bola, posiciones in trayectorias.items():
        for i in range(1, len(posiciones)):
            start_pos = (int(posiciones[i - 1].x), int(posiciones[i - 1].y))
            end_pos = (int(posiciones[i].x), int(posiciones[i].y))
            cv2.line(newframe, start_pos, end_pos, (0, 255, 0), 2)  # Dibuja con color verde y grosor 2
def line_equation(x1, y1, x2, y2):
    A = y2 - y1
    B = x1 - x2
    C = x2*y1 - x1*y2
    return A, B, C
def distance_point_line(x0, y0, A, B, C):
    return abs(A*x0 + B*y0 + C) / (A**2 + B**2)**0.5
def calcular_vector_direccion(punto_inicial, punto_final):
    dx = punto_final[0] - punto_inicial[0]
    dy = punto_final[1] - punto_inicial[1]
    longitud = (dx**2 + dy**2)**0.5
    return (dx / longitud, dy / longitud) 
def calcular_distancia_entre_bolas(bola1, bola2):
    return math.sqrt((bola1[0] - bola2[0])**2 + (bola1[1] - bola2[1])**2)

def cargar_datos_esquinas(archivo_json):
    with open(archivo_json, 'r') as file:
        data = json.load(file)
        esquinas = data['l_circle_screen']
        return esquinas

archivo_json = 'data.json'  # Asegúrate de que la ruta al archivo sea correcta
esquinas = cargar_datos_esquinas(archivo_json)

def calcular_dimensiones(esquinas):
    if len(esquinas) != 4:
        raise ValueError("Se requieren exactamente cuatro esquinas")

    # Asumiendo que las esquinas están ordenadas correctamente
    ancho = np.linalg.norm(np.array(esquinas[0]) - np.array(esquinas[2]))
    alto = np.linalg.norm(np.array(esquinas[0]) - np.array(esquinas[1]))

    return ancho, alto

ancho_mesa, alto_mesa = calcular_dimensiones(esquinas)

def crear_bandas(space, dimensiones_mesa, grosor_banda=10):
    # Definir las bandas de la mesa
    bordes = [
        pymunk.Segment(space.static_body, (0, 0), (dimensiones_mesa[0], 0), grosor_banda),  # Banda superior
        pymunk.Segment(space.static_body, (0, 0), (0, dimensiones_mesa[1]), grosor_banda),  # Banda izquierda
        pymunk.Segment(space.static_body, (dimensiones_mesa[0], 0), dimensiones_mesa, grosor_banda),  # Banda derecha
        pymunk.Segment(space.static_body, (0, dimensiones_mesa[1]), dimensiones_mesa, grosor_banda)   # Banda inferior
    ]
    for borde in bordes:
        borde.elasticity = 0.95
        borde.friction = 0.5
        space.add(borde)

while True:
    t_frame = time.time()
    ret, frame = cap.read()
    nextframe = frame[:,:,2].copy()
    nextframe = cv2.warpPerspective(nextframe, m_camera2screen, (1920,1080), flags=cv2.INTER_LINEAR)
    nextframe = cv2.absdiff(background, nextframe)
    nextframe = cv2.GaussianBlur(nextframe,(5,5),0)
    _, nextframe = cv2.threshold(nextframe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(nextframe, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    newframe = fond.copy()
    l=[]
    taco_detectado = False
    #cv2.circle(newframe, (1344, 536), 27, (255, 0, 255), 10)
    for c in contours:
        M = cv2.moments(c)
        if M["m00"]<np.pi*25**2:
            continue
        lX=[x for [[x, _]] in c]
        lY=[y for [[_, y]] in c]
        if np.corrcoef(lX, lY)[0, 1]**2 > 0.75:
            [vx,vy,x,y] = cv2.fitLine(c, cv2.DIST_L2, 0, 0.01, 0.01).flatten()
            punto_inicial = (int(x + vx * 1920), int(y + vy * 1920))
            punto_final = (int(x + vx * -1920), int(y + vy * -1920))
            taco_detectado = True
            continue
        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])
        ecartype = np.std([((x-ix)**2 + (y-iy)**2)**0.5 for ix, iy in zip(lX, lY)])
        if ecartype < 10:
            l+=[(x, y)]
    if taco_detectado:
        space = pymunk.Space()
        space.gravity = (0, 0)
        
        # Definir dimensiones de la mesa (ajustar según sea necesario)
        dimensiones_mesa = (ancho_mesa, alto_mesa)
        crear_bandas(space, dimensiones_mesa)
        
        bolas_pymunk = [crear_bola(space, pos) for pos in l]
        direccion_taco = calcular_vector_direccion(punto_inicial, punto_final)
        A, B, C = line_equation(*punto_inicial, *punto_final)
        radio_bola = 27  
        bola_mas_cercana = None
        distancia_minima = float('inf')
        for xb, yb in l:
            dist = distance_point_line(xb, yb, A, B, C)
            distancia_al_taco = calcular_distancia_entre_bolas(punto_inicial, (xb, yb))
            if dist <= radio_bola and distancia_al_taco < distancia_minima:
                direccion_a_la_bola = calcular_vector_direccion(punto_inicial, (xb, yb))
                if direccion_a_la_bola[0] * direccion_taco[0] + direccion_a_la_bola[1] * direccion_taco[1] > 0:
                    distancia_minima = distancia_al_taco
                    bola_mas_cercana = (xb, yb)
                print(f"La línea del taco choca con la bola en ({xb}, {yb})")
                if bola_mas_cercana:
                    
                    # Aplicar impulso a la bola más cercana al taco
                    direccion_taco = calcular_vector_direccion(punto_inicial, punto_final)
                    for bola in bolas_pymunk:
                        if (int(bola.position.x), int(bola.position.y)) == bola_mas_cercana:
                            impulso = pymunk.Vec2d(*direccion_taco) * 2000
                            aplicar_impulso(bola, impulso)
                            break
                    # Simular movimientos y obtener trayectorias
                    trayectorias = simular_movimientos_y_obtener_trayectorias(space, bolas_pymunk, steps=100)

                    # Dibujar las trayectorias resultantes
                    dibujar_trayectorias(trayectorias, newframe)
                    cv2.line(newframe, punto_inicial, bola_mas_cercana, (255, 255, 255), 15)
                        
    Ball.mapping_detecting_balls(t_frame - debut_time, l)
    for ball in Ball.lBall:
        x, y, vx, vy, v = ball.interpolation((time.time() - t_prediction) + 0.4)
        x, y = int(x), int(y)
        zoom = 0.7
        cv2.circle(newframe, (x, y), 50, (255, 255, 255), 10)
        if v > 0:
            cv2.arrowedLine(newframe,
                            (int(x), int(y)),
                            (int(x+vx*zoom), int(y+vy*zoom)),
                            (255, 255, 255),
                            10)
            if len(ball.lChemin)>=2:
                pts = np.array(ball.lChemin + ball.lVt1[::-1],
                          np.int32).reshape((-1, 1, 2))
                chemin = np.array(ball.lChemin + [[x,y]], np.int32).reshape((-1, 1, 2))
                vdx, vdy = np.array([x,y]) - np.array(ball.lChemin[-1])
                vitesse = np.array(ball.lVt1 +
                                    [[ball.lVt1[-1][0]+vdx, ball.lVt1[-1][1]+vdy]] +
                                    [[ball.lVt2[-1][0]+vdx, ball.lVt2[-1][1]+vdy]] +
                                     ball.lVt2[::-1], np.int32).reshape((-1, 1, 2))
                cv2.fillPoly(newframe, [vitesse], (255, 0, 0))
                cv2.polylines(newframe, [vitesse], True, (0, 0, 255), 2)
                cv2.polylines(newframe, [chemin], False, (255, 255, 255), 2)
                vu = np.array(ball.lVt1[0]) - np.array(ball.lChemin[0])
                vu /= np.linalg.norm(vu)
                s=55
                cv2.arrowedLine(newframe,
                                tuple(map(int, ball.lChemin[0])),
                                tuple(map(int, np.array(ball.lChemin[0]) + vu*s)),
                                (255, 255, 255),
                                2)
                cv2.arrowedLine(newframe,
                                tuple(map(int, ball.lChemin[0])),
                                tuple(map(int, np.array(ball.lChemin[0]) - vu*s)),
                                (255, 255, 255),
                                2)
                cv2.putText(newframe,
                            "Speed(px/s)",
                            tuple(map(int, ball.lChemin[1])),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA)
                prediction = np.array([[[x,y]] for t,x,y in ball.lPos_prediction], np.int32)
                cv2.polylines(newframe, [prediction], False, (0, 255, 0), 4)
        cv2.circle(newframe,
                   tuple(map(int, ball.body.position)),
                   int(Ball.radius),
                   (0, 255, 0),
                   -1)
        font_scale = cv2.getFontScaleFromHeight(cv2.FONT_HERSHEY_SIMPLEX, 30, 3) 
        cv2.putText(newframe,
                    "ID:" + chr(ord('A') + ball.id),
                    (int(x + Ball.radius*2.2), y + 33),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA)
        cv2.putText(newframe,
                    "V=" + str(round(v)),
                    (int(x + Ball.radius*2.2), y-3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA)
    cv2.putText(newframe,
                "FPS: " + str(int(1/(time.time() - t_frame))),
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                2,
                (255, 255, 255),
                3,
                cv2.LINE_AA)
    n_frame+=1
    step = 1/120
    n = int((time.time() - debut_time - t_physic_engine) / step)
    for i in range(n):
        space.step(step)
    t_physic_engine += step*n
    t_prediction = time.time()
    newframe = cv2.warpPerspective(newframe, m_projector2camera, (1920,1080), flags=cv2.INTER_LINEAR)
    cv2.imshow('Billard', newframe)
    k = cv2.waitKey(1) & 0xff
    if k == 27:
        break
    idBall = k - ord('a')
    if idBall in [b.id for b in Ball.lBall]:
        ball = Ball.lBall[idBall]
        fig, axs = plt.subplots(2, 2)
        lVt = [t for t,vx,vy,v in ball.lVitesse]
        lVv = [v for t,vx,vy,v in ball.lVitesse]
        axs[0, 0].plot(lVt, lVv, 'o-')
        axs[0, 0].set(xlabel="Time (s)",
                      ylabel="Speed (px/s)",
                      title="Speed of the ball")
        axs[0, 0].legend(loc='best')
        a = np.array(ball.lAcc)
        axs[0, 1].plot(a[:,0], a[:,1], 'o-')
        axs[0, 1].set(xlabel="Time (s)",
                      ylabel="Acceleration (px/s²)",
                      title="Acceleration of the ball")
        lT = [t for t,x,y in ball.lPos]
        lX = [x for t,x,y in ball.lPos]
        lY = [y for t,x,y in ball.lPos]
        lT_prediction = [t for t,x,y in ball.lPos_prediction]
        lX_prediction = [x for t,x,y in ball.lPos_prediction]
        lY_prediction = [y for t,x,y in ball.lPos_prediction]
        axs[1, 0].plot(lX, lY, 'o-', label='Ball')
        axs[1, 0].plot(lX_prediction, lY_prediction, 'x-', label='Prediction')
        axs[1, 0].set(xlabel="X",
                      ylabel="Y",
                      title="Position of the ball")
        axs[1, 0].legend(loc='best')
        lT = [t for t, a in ball.lAngle]
        lA = [a for t, a in ball.lAngle]
        axs[1, 1].plot(lT, lA, 'o-')
        axs[1, 1].set(xlabel="Time(s)",
                      ylabel="Direction of the ball (radians)",
                      title="Direction of the ball")
        plt.show()
cv2.destroyAllWindows()
cap.release()
exit()