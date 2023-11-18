class Ball:
    # ... (otras definiciones de clase)

    @classmethod
    def mapping_detecting_balls(cls, t, lDetected_ball):
        # Lista para almacenar las bolas mapeadas a las bolas detectadas
        mapped_balls = []

        # Iterar sobre las bolas detectadas
        for detected_ball in lDetected_ball:
            # Obtener las coordenadas de la bola detectada
            x_detected, y_detected = detected_ball

            # Calcular las distancias entre la bola detectada y las bolas existentes
            distances = [(np.sqrt((x - x_detected) ** 2 + (y - y_detected) ** 2), ball) for _, x, y in cls.lPos]

            # Ordenar las distancias de menor a mayor
            distances.sort(key=lambda item: item[0])

            # Tomar la bola más cercana si la distancia es menor que un umbral
            if distances and distances[0][0] < 10:
                _, closest_ball = distances[0]
                # Añadir la bola existente al resultado
                mapped_balls.append(closest_ball)

        # Iterar sobre las bolas existentes y eliminar aquellas que no fueron mapeadas
        for ball in cls.lBall.copy():
            if ball not in mapped_balls:
                ball.__del__()

        # Crear nuevas instancias de la clase Ball para las bolas no mapeadas
        for detected_ball in lDetected_ball:
            if all(ball.distance_to(detected_ball) >= umbral_distancia for ball in mapped_balls):
                cls(t, *detected_ball)

        # Devolver las bolas mapeadas y las bolas recién creadas
        return mapped_balls + [ball for ball in cls.lBall if ball not in mapped_balls]
