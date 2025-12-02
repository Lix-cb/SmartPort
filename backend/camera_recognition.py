import cv2
import numpy as np
import face_recognition as fr

def obtener_embedding_camara():
    return obtener_embedding_camara_headless(headless=False)


def obtener_embedding_camara_headless(headless=True, timeout_seconds=2):
    """Captura un frame de la cÃ¡mara y devuelve el embedding.
    - headless=False: abre una ventana y espera ENTER/SPACE (o ESC para cancelar)
    - headless=True: espera `timeout_seconds` y captura sin GUI (Ãºtil por SSH)
    """
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("No se pudo abrir la cÃ¡mara.")
        return None

    frame = None

    if headless:
        import time
        time.sleep(timeout_seconds)
        ret, frame = cam.read()
    else:
        window_name = "VerificaciÃ³n Facial"
        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        except Exception:
            pass

        print("Presiona ENTER/SPACE para capturar, ESC para cancelar...")
        import time
        start = time.time()
        frame = None
        while True:
            ret, frame = cam.read()
            if not ret:
                continue
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (13, 10, 32):
                break
            if key == 27:
                frame = None
                break
            if time.time() - start > 10:
                break
        try:
            cv2.destroyWindow(window_name)
        except Exception:
            cv2.destroyAllWindows()

    cam.release()
    if not headless:
        cv2.destroyAllWindows()

    if frame is None:
        print("No se obtuvo imagen de la cÃ¡mara.")
        return None

    # Detectar rostro con la librerÃ­a 'face_recognition'
    loc = fr.face_locations(frame)
    if len(loc) == 0:
        print("No se detectÃ³ rostro.")
        return None

    encoding = fr.face_encodings(frame, loc)[0]
    return np.array(encoding)

def verificar_persona(embedding_bd):
    emb_actual = obtener_embedding_camara_headless(headless=True)

    if emb_actual is None:
        return False

    distancia = np.linalg.norm(embedding_bd - emb_actual)
    print("Distancia facial:", distancia)

    return distancia < 0.6