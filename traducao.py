import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import json
import os
import math

# Arquivo de gestos
ARQUIVO_GESTOS = "gestos_salvos.json"

# -------------------------
# Utilitários de arquivo
# -------------------------
def carregar_gestos():
    """Carrega e normaliza os gestos do arquivo (se existirem)."""
    if not os.path.exists(ARQUIVO_GESTOS):
        return {}
    try:
        with open(ARQUIVO_GESTOS, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {}

    # Normaliza todos os gestos carregados para garantir formato consistente
    gestos_norm = {}
    for nome, coords in raw.items():
        try:
            gestos_norm[nome] = normalizar_landmarks(coords)
        except Exception:
            # se der erro, ignora esse gesto
            continue
    return gestos_norm


def salvar_gestos(gestos):
    """Salva gestos (assume que já estão normalizados)."""
    with open(ARQUIVO_GESTOS, "w", encoding="utf-8") as f:
        json.dump(gestos, f, ensure_ascii=False, indent=4)


# -------------------------
# Mediapipe config
# -------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


# -------------------------
# Normalização e distância
# -------------------------
def normalizar_landmarks(landmarks):
    """
    Normaliza uma lista de 21 landmarks [(x,y,z), ...]:
    1) Centraliza em relação ao landmark 0 (punho)
    2) Divide por uma medida de escala (distância média) para invariância de escala
    Retorna lista de listas [ [x',y',z'], ... ].
    """
    if not landmarks or len(landmarks) == 0:
        return []

    pts = [[float(p[0]), float(p[1]), float(p[2])] for p in landmarks]

    # base: primeiro ponto (punho)
    base_x, base_y, base_z = pts[0]

    # centralizar
    centralizados = [[p[0] - base_x, p[1] - base_y, p[2] - base_z] for p in pts]

    # calcular uma medida de escala: média das distâncias ao centro
    soma = 0.0
    for p in centralizados:
        soma += math.sqrt(p[0]**2 + p[1]**2 + p[2]**2)
    escala = soma / len(centralizados) if len(centralizados) > 0 else 1.0

    if escala == 0:
        escala = 1.0

    normalizados = [[p[0] / escala, p[1] / escala, p[2] / escala] for p in centralizados]
    # converter para listas simples
    return normalizados


def media_distancia(a, b):
    """
    Calcula distância média entre duas listas de pontos (mesmo comprimento).
    """
    if not a or not b or len(a) != len(b):
        return float("inf")
    s = 0.0
    for p1, p2 in zip(a, b):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dz = p1[2] - p2[2]
        s += math.sqrt(dx*dx + dy*dy + dz*dz)
    return s / len(a)


# -------------------------
# Reconhecimento (TRADUÇÃO)
# -------------------------
def abrir_camera_traducao():
    """
    Abre janela Tkinter com câmera em cima e texto do gesto reconhecido embaixo.
    Usa comparação por distância média entre landmarks normalizados.
    """
    # carregar gestos normalizados
    gestos_salvos = carregar_gestos()

    janela = tk.Toplevel()
    janela.title("Tradução em Tempo Real")
    janela.geometry("900x700")

    # camera label (imagem)
    lbl_camera = tk.Label(janela)
    lbl_camera.pack(pady=10)

    # saída de texto (embaixo)
    lbl_saida = tk.Label(janela, text="Gesto: ---", font=("Segoe UI", 20, "bold"))
    lbl_saida.pack(pady=10)

    # inicializa câmera e mediapipe
    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1,
                           model_complexity=1,
                           min_detection_confidence=0.6,
                           min_tracking_confidence=0.6)

    # parâmetros ajustáveis
    LIMIAR_RECONHECIMENTO = 0.30  # quanto menor → mais rígido; ajuste conforme necessidade

    def reconhecer_por_coords(coords_atual):
        """Normaliza coords_atual e compara com gestos_salvos, retornando nome ou '---'."""
        if not gestos_salvos:
            return "---"
        atual_norm = normalizar_landmarks(coords_atual)

        melhor = None
        melhor_val = float("inf")

        for nome, coords_salvas in gestos_salvos.items():
            # coords_salvas já foram normalizados ao carregar
            d = media_distancia(atual_norm, coords_salvas)
            if d < melhor_val:
                melhor_val = d
                melhor = nome

        if melhor is None:
            return "---"

        if melhor_val <= LIMIAR_RECONHECIMENTO:
            return melhor
        return "---"

    def atualizar():
        ret, frame = cap.read()
        if not ret:
            janela.after(10, atualizar)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        resultado = hands.process(rgb)
        gesto_atual = "---"

        if resultado.multi_hand_landmarks:
            # pega primeira mão
            hand_landmarks = resultado.multi_hand_landmarks[0]

            # desenhar landmarks na imagem
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2)
            )

            # extrair coords
            coords = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]

            # reconhecimento real
            gesto_atual = reconhecer_por_coords(coords)

        # atualizar label de texto
        lbl_saida.config(text=f"Gesto: {gesto_atual}")

        # converter frame para Tkinter e mostrar
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        # opcional: resize para garantir boa visualização dentro da janela
        # img = img.resize((800, 560))
        imgtk = ImageTk.PhotoImage(image=img)
        lbl_camera.imgtk = imgtk
        lbl_camera.configure(image=imgtk)

        janela.after(10, atualizar)

    atualizar()

    def fechar():
        try:
            cap.release()
        except:
            pass
        janela.destroy()

    janela.protocol("WM_DELETE_WINDOW", fechar)


# -------------------------
# Salvar Gestos (com botão)
# -------------------------
def abrir_camera_salvar_gesto():
    """
    Janela para salvar gesto manualmente: mostra câmera, tem campo nome e botão 'Salvar Gesto'.
    Salva a versão NORMALIZADA do gesto no JSON.
    """
    janela = tk.Toplevel()
    janela.title("Salvar Novo Gesto – Libras")
    janela.geometry("900x700")

    lbl_camera = tk.Label(janela)
    lbl_camera.pack(pady=10)

    tk.Label(janela, text="Nome do gesto:", font=("Segoe UI", 12)).pack()
    entry_nome = tk.Entry(janela, font=("Segoe UI", 12))
    entry_nome.pack(pady=5)

    lbl_status = tk.Label(janela, text="", font=("Segoe UI", 12))
    lbl_status.pack(pady=5)

    btn_salvar = tk.Button(janela, text="Salvar Gesto", font=("Segoe UI", 12), bg="#c8e6c9")
    btn_salvar.pack(pady=10)

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1,
                           model_complexity=1,
                           min_detection_confidence=0.6,
                           min_tracking_confidence=0.6)

    gestos_existentes = carregar_gestos()  # carregados já normalizados
    ultimo_coords = None

    def capturar():
        nonlocal ultimo_coords
        ret, frame = cap.read()
        if not ret:
            janela.after(10, capturar)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        resultado = hands.process(rgb)
        ultimo_coords = None

        if resultado.multi_hand_landmarks:
            hand_landmarks = resultado.multi_hand_landmarks[0]

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2)
            )

            ultimo_coords = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]

        # mostrar frame
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        lbl_camera.imgtk = imgtk
        lbl_camera.configure(image=imgtk)

        janela.after(10, capturar)

    capturar()

    def salvar_click():
        nonlocal ultimo_coords, gestos_existentes
        nome = entry_nome.get().strip()
        if not nome:
            lbl_status.config(text="Digite um nome válido!", fg="red")
            return
        if ultimo_coords is None:
            lbl_status.config(text="Nenhuma mão detectada!", fg="red")
            return

        # normaliza e salva
        normalizado = normalizar_landmarks(ultimo_coords)
        gestos_existentes[nome] = normalizado
        salvar_gestos(gestos_existentes)
        lbl_status.config(text=f"Gesto '{nome}' salvo!", fg="green")

    btn_salvar.config(command=salvar_click)

    def fechar():
        try:
            cap.release()
        except:
            pass
        janela.destroy()

    janela.protocol("WM_DELETE_WINDOW", fechar)
