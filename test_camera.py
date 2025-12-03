import cv2
import time

print("Probando Logitech HD Pro Webcam...")

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

if cap.isOpened():
    print("✓ Cámara abierta")
    
    # Configurar
    cap.set(cv2. CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    time.sleep(2)
    
    # Descartar primeros frames
    for _ in range(5):
        cap.read()
    
    # Leer frame de prueba
    ret, frame = cap.read()
    
    if ret and frame is not None:
        print(f"✓ Frame capturado: {frame.shape}")
    else:
        print("✗ No se pudo capturar frame")
    
    cap.release()
else:
    print("✗ No se pudo abrir la cámara")
