import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import json
import os
import math

# ===============================
# Arquivos de dados
# ===============================
ARQUIVO_GESTOS = "gestos_salvos.json"
ARQUIVO_FRASES = "frases_salvas.json"

# ===============================
# Utilitários
# ===============================
def carregar_gestos():
    if os.path.exists(ARQUIVO_GESTOS):
        try:
            with open(ARQUIVO_GESTOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_gestos(gestos):
    with open(ARQUIVO_GESTOS, "w", encoding="utf-8") as f:
        json.dump(gestos, f, ensure_ascii=False, indent=4)

def carregar_frases():
    if os.path.exists(ARQUIVO_FRASES):
        try:
            with open(ARQUIVO_FRASES, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"frases": []}
    return {"frases": []}

def salvar_frases(frases):
    with open(ARQUIVO_FRASES, "w", encoding="utf-8") as f:
        json.dump(frases, f, ensure_ascii=False, indent=4)

# ===============================
# Mediapipe
# ===============================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# ===============================
# Normalização e Distância
# ===============================
def normalizar_landmarks(landmarks):
    if not landmarks or len(landmarks) == 0:
        return []

    pts = [[float(p[0]), float(p[1]), float(p[2])] for p in landmarks]
    base_x, base_y, base_z = pts[0]
    centralizados = [[p[0]-base_x, p[1]-base_y, p[2]-base_z] for p in pts]

    soma = sum([math.sqrt(p[0]**2+p[1]**2+p[2]**2) for p in centralizados])
    escala = soma / len(centralizados) if len(centralizados)>0 else 1.0
    if escala == 0: escala = 1.0

    normalizados = [[p[0]/escala, p[1]/escala, p[2]/escala] for p in centralizados]
    return normalizados

def media_distancia(a,b):
    if not a or not b or len(a)!=len(b):
        return float("inf")
    s = sum([math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)
             for p1,p2 in zip(a,b)])
    return s/len(a)

# ===============================
# Função de tradução
# ===============================
def abrir_camera_traducao():
    gestos_salvos = carregar_gestos()
    frases_salvas = carregar_frases()

    janela = tk.Toplevel()
    janela.title("Tradução em Tempo Real")
    janela.geometry("900x700")

    lbl_camera = tk.Label(janela)
    lbl_camera.pack(pady=10)

    lbl_saida_gesto = tk.Label(janela, text="Gesto: ---", font=("Segoe UI", 20, "bold"))
    lbl_saida_gesto.pack(pady=5)

    lbl_saida_frase = tk.Label(janela, text="", font=("Segoe UI", 18, "bold"), fg="blue")
    lbl_saida_frase.pack(pady=5)

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1,
                           model_complexity=1,
                           min_detection_confidence=0.6,
                           min_tracking_confidence=0.6)

    LIMIAR_RECONHECIMENTO = 0.40
    gestos_recentes = []
    frase_atual = ""

    def reconhecer_por_coords(coords_atual):
        atual_norm = normalizar_landmarks(coords_atual)
        melhor = None
        melhor_val = float("inf")

        for nome, coords_salvas in gestos_salvos.items():
            d = media_distancia(atual_norm, coords_salvas)
            if d < melhor_val:
                melhor_val = d
                melhor = nome
        if melhor_val <= LIMIAR_RECONHECIMENTO:
            return melhor
        return "---"

    def atualizar():
        nonlocal gestos_recentes, frase_atual
        ret, frame = cap.read()
        if not ret:
            janela.after(10, atualizar)
            return

        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = hands.process(rgb)
        gesto_atual = "---"

        if resultado.multi_hand_landmarks:
            hand_landmarks = resultado.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            coords = [(lm.x,lm.y,lm.z) for lm in hand_landmarks.landmark]
            gesto_atual = reconhecer_por_coords(coords)

            # Atualiza lista de gestos recentes
            if gesto_atual != "---":
                if len(gestos_recentes) == 0 or gestos_recentes[-1] != gesto_atual:
                    gestos_recentes.append(gesto_atual)
                    # Limita tamanho da lista
                    if len(gestos_recentes) > 10:
                        gestos_recentes.pop(0)

            # Verifica se a sequência de gestos corresponde a alguma frase
            frase_encontrada = False
            for f in frases_salvas.get("frases", []):
                seq = f["sequencia"]
                if len(gestos_recentes) >= len(seq) and gestos_recentes[-len(seq):] == seq:
                    frase_atual = f["nome"]
                    frase_encontrada = True
                    break
            if not frase_encontrada:
                frase_atual = ""

        lbl_saida_gesto.config(text=f"Gesto: {gesto_atual}")
        lbl_saida_frase.config(text=f"Frase: {frase_atual}")

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        lbl_camera.imgtk = imgtk
        lbl_camera.configure(image=imgtk)

        janela.after(10, atualizar)

    atualizar()

    def fechar():
        try: cap.release()
        except: pass
        janela.destroy()

    janela.protocol("WM_DELETE_WINDOW", fechar)

# ===============================
# Função de salvar gestos
# ===============================
def abrir_camera_salvar_gesto():
    janela = tk.Toplevel()
    janela.title("Salvar Novo Gesto – Libras")
    janela.geometry("900x700")

    lbl_camera = tk.Label(janela)
    lbl_camera.pack(pady=10)

    tk.Label(janela, text="Nome do gesto:", font=("Segoe UI",12)).pack()
    entry_nome = tk.Entry(janela,font=("Segoe UI",12))
    entry_nome.pack(pady=5)

    lbl_status = tk.Label(janela, text="", font=("Segoe UI",12))
    lbl_status.pack(pady=5)

    btn_salvar = tk.Button(janela, text="Salvar Gesto", font=("Segoe UI",12), bg="#c8e6c9")
    btn_salvar.pack(pady=10)

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1,
                           model_complexity=1,
                           min_detection_confidence=0.6,
                           min_tracking_confidence=0.6)

    gestos_existentes = carregar_gestos()
    ultimo_coords = None

    def capturar():
        nonlocal ultimo_coords
        ret, frame = cap.read()
        if not ret:
            janela.after(10, capturar)
            return
        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = hands.process(rgb)
        ultimo_coords = None
        if resultado.multi_hand_landmarks:
            hand_landmarks = resultado.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            ultimo_coords = [(lm.x,lm.y,lm.z) for lm in hand_landmarks.landmark]

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        lbl_camera.imgtk = imgtk
        lbl_camera.configure(image=imgtk)

        janela.after(10, capturar)

    capturar()

    def salvar_click():
        nonlocal ultimo_coords
        nome = entry_nome.get().strip()
        if not nome:
            lbl_status.config(text="Digite um nome válido!", fg="red")
            return
        if ultimo_coords is None:
            lbl_status.config(text="Nenhuma mão detectada!", fg="red")
            return
        normalizado = normalizar_landmarks(ultimo_coords)
        gestos_existentes[nome] = normalizado
        salvar_gestos(gestos_existentes)
        lbl_status.config(text=f"Gesto '{nome}' salvo!", fg="green")

    btn_salvar.config(command=salvar_click)

    def fechar():
        try: cap.release()
        except: pass
        janela.destroy()

    janela.protocol("WM_DELETE_WINDOW", fechar)

# ===============================
# Função de cadastrar frases
# ===============================
def cadastrar_frases():
    janela = tk.Toplevel()
    janela.title("Cadastrar Frases – Libras")
    janela.geometry("600x400")

    tk.Label(janela, text="Frase:", font=("Segoe UI",12)).pack()
    entry_frase = tk.Entry(janela,font=("Segoe UI",12))
    entry_frase.pack(pady=5)

    tk.Label(janela, text="Sequência de gestos (separados por vírgula):", font=("Segoe UI",12)).pack()
    entry_sequencia = tk.Entry(janela,font=("Segoe UI",12))
    entry_sequencia.pack(pady=5)

    lbl_status = tk.Label(janela, text="", font=("Segoe UI",12))
    lbl_status.pack(pady=5)

    btn_salvar = tk.Button(janela,text="Salvar Frase",font=("Segoe UI",12),bg="#c8e6c9")
    btn_salvar.pack(pady=10)

    frases = carregar_frases().get("frases", [])

    def salvar_click():
        frase = entry_frase.get().strip()
        sequencia = [g.strip().capitalize() for g in entry_sequencia.get().split(",") if g.strip()]
        if not frase or not sequencia:
            lbl_status.config(text="Preencha todos os campos!", fg="red")
            return
        frases.append({"nome": frase, "sequencia": sequencia})
        salvar_frases({"frases": frases})
        lbl_status.config(text=f"Frase '{frase}' salva!", fg="green")
        entry_frase.delete(0,tk.END)
        entry_sequencia.delete(0,tk.END)

    btn_salvar.config(command=salvar_click)
