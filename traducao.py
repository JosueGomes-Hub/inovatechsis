import tkinter as tk
from tkinter import messagebox
import cv2
import mediapipe as mp
import numpy as np
import json
import os

GESTOS_PATH = "gestos_salvos.json"

# ---------------------
#   CARREGAR / SALVAR
# ---------------------

def carregar_gestos():
    if not os.path.exists(GESTOS_PATH):
        return {}
    try:
        with open(GESTOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def salvar_gestos(gestos):
    with open(GESTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(gestos, f, indent=4, ensure_ascii=False)


# -------------------------------
#    NORMALIZAÇÃO DOS GESTOS
# -------------------------------

def normalizar_pontos(pontos):
    """
    Normaliza os pontos da mão para comparação.
    """
    pts = np.array(pontos).reshape(-1, 3)
    centro = np.mean(pts, axis=0)
    pts -= centro
    max_val = np.max(np.abs(pts))
    if max_val > 0:
        pts /= max_val
    return pts.flatten()


# -------------------------------
#   RECONHECER GESTOS (TRADUÇÃO)
# -------------------------------

def abrir_camera_traducao():
    gestos_salvos = carregar_gestos()
    if not gestos_salvos:
        messagebox.showerror("Erro", "Nenhum gesto salvo para reconhecer.")
        return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
    cap = cv2.VideoCapture(0)

    messagebox.showinfo("Tradução", "A câmera será aberta para reconhecer gestos.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        gesto_detectado = "Nenhum gesto"

        if result.multi_hand_landmarks:
            mão = result.multi_hand_landmarks[0]
            pontos = [[lm.x, lm.y, lm.z] for lm in mão.landmark]
            norm = normalizar_pontos(pontos)

            menor_dist = 9999
            melhor_nome = None

            # COMPARAR COM GESTOS SALVOS
            for nome, pontos_salvos in gestos_salvos.items():
                pontos_salvos = np.array(pontos_salvos)
                dist = np.linalg.norm(norm - pontos_salvos)

                if dist < menor_dist:
                    menor_dist = dist
                    melhor_nome = nome

            if menor_dist < 0.5:
                gesto_detectado = melhor_nome

        cv2.putText(frame, f"Gesto: {gesto_detectado}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.imshow("Traducao em tempo real", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# -------------------------------
#    SALVAR NOVO GESTO
# -------------------------------

def abrir_camera_salvar_gesto():
    janela = tk.Toplevel()
    janela.title("Salvar novo gesto")

    tk.Label(janela, text="Nome do gesto:", font=("Arial", 12)).pack(pady=5)
    entry = tk.Entry(janela, font=("Arial", 12))
    entry.pack(pady=5)

    tk.Button(janela, text="Iniciar captura",
              command=lambda: capturar_gesto(entry.get().strip(), janela)
              ).pack(pady=10)


def capturar_gesto(nome_gesto, janela):
    if not nome_gesto:
        messagebox.showerror("Erro", "Dê um nome para o gesto.")
        return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
    cap = cv2.VideoCapture(0)

    messagebox.showinfo("Captura", "A câmera irá abrir.\nPressione 's' para salvar o gesto.")

    pontos_final = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        if result.multi_hand_landmarks:
            mão = result.multi_hand_landmarks[0]
            pontos = [[lm.x, lm.y, lm.z] for lm in mão.landmark]
            pontos_final = normalizar_pontos(pontos)

            cv2.putText(frame, "Pressione S para salvar", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        cv2.imshow("Capturando gesto", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s") and pontos_final is not None:
            break
        if key == ord("q"):
            pontos_final = None
            break

    cap.release()
    cv2.destroyAllWindows()

    if pontos_final is None:
        messagebox.showerror("Erro", "Nenhum gesto foi salvo.")
        return

    gestos = carregar_gestos()
    gestos[nome_gesto] = pontos_final.tolist()
    salvar_gestos(gestos)

    messagebox.showinfo("Sucesso", f"Gesto '{nome_gesto}' salvo!")
