import cv2
import mediapipe as mp

def iniciar_traducao():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    # Inicializa o detector de mãos
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    cap = cv2.VideoCapture(0)  # abre a câmera (0 = webcam padrão)
    print("Pressione 'q' para sair")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Não conseguiu acessar a câmera.")
            break

        # Converte a imagem para RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        # Volta para BGR para exibir com OpenCV
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Se detectar mãos
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        cv2.imshow('Tradutor LIBRAS - InovatechSIS', image)

        # Fecha com 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()