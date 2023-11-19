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
def norma(vector):
    return math.sqrt(vector[0]**2 + vector[1]**2)
def calcular_punto_impacto(xb, yb, radio_bola, direccion_taco):
    norma_direccion = norma(direccion_taco)
    direccion_normalizada = (direccion_taco[0] / norma_direccion, direccion_taco[1] / norma_direccion)
    punto_mas_cercano = (xb + direccion_normalizada[0] * radio_bola, yb + direccion_normalizada[1] * radio_bola)
    return punto_mas_cercano
def calcular_direccion_reflejada(direccion_taco, direccion_normal):
    proyeccion = sum(dt * dn for dt, dn in zip(direccion_taco, direccion_normal))
    return tuple(dt - 2 * proyeccion * dn for dt, dn in zip(direccion_taco, direccion_normal))
def calcular_distancia_entre_bolas(bola1, bola2):
    return math.sqrt((bola1[0] - bola2[0])**2 + (bola1[1] - bola2[1])**2)
def calcular_direccion_post_colision(punto_impacto, bola_objetivo, direccion_reflejada):
    dx = bola_objetivo[0] - punto_impacto[0]
    dy = bola_objetivo[1] - punto_impacto[1]
    longitud = math.sqrt(dx**2 + dy**2)
    return (dx / longitud, dy / longitud)
def distancia_punto_linea(px, py, x1, y1, x2, y2):
    numerador = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1)
    denominador = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    return numerador / denominador
def calcular_direccion_normal(punto_impacto, centro_bola):
    dx = centro_bola[0] - punto_impacto[0]
    dy = centro_bola[1] - punto_impacto[1]
    longitud = math.sqrt(dx**2 + dy**2)
    return (-dy / longitud, dx / longitud)
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
    for c in contours:
        M = cv2.moments(c)
        if M["m00"]<np.pi*25**2:
            continue
        lX=[x for [[x, _]] in c]
        lY=[y for [[_, y]] in c]
        if np.corrcoef(lX, lY)[0, 1]**2 > 0.75:
            [vx,vy,x,y] = cv2.fitLine(c, cv2.DIST_L2, 0, 0.01, 0.01)
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
                    punto_impacto = calcular_punto_impacto(*bola_mas_cercana, radio_bola, direccion_taco)
                    cv2.line(newframe, punto_inicial, bola_mas_cercana, (255, 255, 255), 15)
                    print(f"Punto de impacto: {punto_impacto}")
                    direccion_normal = calcular_direccion_normal(punto_impacto, bola_mas_cercana)
                    direccion_reflejada = calcular_direccion_reflejada(direccion_taco, direccion_normal)
                    print(f"Direccion de la bola: {direccion_reflejada}")
                    longitud_linea = 1920  
                    punto_final_reflejado = (int(punto_impacto[0] + direccion_reflejada[0] * longitud_linea),
                                        int(punto_impacto[1] + direccion_reflejada[1] * longitud_linea))
                    punto_final_reflejado = tuple(map(int, punto_final_reflejado))
                    punto_impacto = tuple(map(int, punto_impacto))
                    punto_final_trayectoria = (int(punto_impacto[0] + direccion_reflejada[0] * longitud_linea),
                                            int(punto_impacto[1] + direccion_reflejada[1] * longitud_linea))
                    bola_siguiente_colision = None
                    distancia_minima_siguiente = float('inf')
                    for bola_estatica in l:
                        if bola_estatica != bola_mas_cercana: 
                            distancia_linea = distancia_punto_linea(bola_estatica[0], bola_estatica[1],
                                                                    punto_impacto[0], punto_impacto[1],
                                                                    punto_final_reflejado[0], punto_final_reflejado[1])
                            if distancia_linea < radio_bola * 2:
                                distancia_actual = calcular_distancia_entre_bolas(punto_impacto, bola_estatica)
                                if distancia_actual < distancia_minima_siguiente:
                                    distancia_minima_siguiente = distancia_actual
                                    bola_siguiente_colision = bola_estatica
                    if bola_siguiente_colision:
                        punto_final_ajustado = calcular_punto_impacto(*bola_siguiente_colision, radio_bola, direccion_reflejada)
                        punto_final_ajustado = tuple(map(int, punto_final_ajustado))
                        cv2.line(newframe, punto_impacto, punto_final_ajustado, (0, 255, 0), 5)
                    else:
                        punto_final_reflejado = tuple(map(int, punto_final_reflejado))
                        cv2.line(newframe, punto_impacto, punto_final_reflejado, (0, 255, 0), 5)
                    bola_objetivo = None
                    distancia_minima = float('inf')
                    for bola_estatica in l:
                        if bola_estatica != (xb, yb): 
                            distancia_linea = distancia_punto_linea(bola_estatica[0], bola_estatica[1],
                                                                    punto_impacto[0], punto_impacto[1],
                                                                    punto_final_trayectoria[0], punto_final_trayectoria[1])
                            if distancia_linea < radio_bola * 2 and distancia_minima > calcular_distancia_entre_bolas(punto_impacto, bola_estatica):
                                distancia_minima = calcular_distancia_entre_bolas(punto_impacto, bola_estatica)
                                bola_objetivo = bola_estatica
                    if bola_objetivo:
                        nueva_direccion = calcular_direccion_post_colision(punto_impacto, bola_objetivo, direccion_reflejada)
                        punto_final_nueva_direccion = (int(bola_objetivo[0] + nueva_direccion[0] * longitud_linea),
                                                    int(bola_objetivo[1] + nueva_direccion[1] * longitud_linea))
                        punto_final_nueva_direccion = tuple(map(int, punto_final_nueva_direccion))
                        cv2.line(newframe, bola_objetivo, punto_final_nueva_direccion, (255, 0, 0), 5)