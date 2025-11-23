import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import json
import os
from traducao import abrir_camera_traducao, abrir_camera_salvar_gesto, cadastrar_frases

#AVISO: estou utilizando pyhton 3.11 pois o mediapipe não funciona em versões mais recentes.

BAU_PATH = "bau_de_valores.json"

def carregar_usuarios():
    if os.path.exists(BAU_PATH):
        try:
            with open(BAU_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salvar_usuarios(usuarios):
    with open(BAU_PATH, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False)


def show_main_menu():
    for widget in app.winfo_children():
        widget.destroy()
    app.title("Menu Principal")
    tk.Label(app, text="Bem-vindo ao Menu Principal!", font=('Arial', 16), bg=BG_COLOR).pack(pady=10)
    tk.Button(app, text="Alfabeto", width=20, font=FONT, command=mostrar_alfabeto).pack(pady=5)
    tk.Button(app, text="Frase Simples", width=20, font=FONT, command=mostrar_frases_simples).pack(pady=5)
    tk.Button(app, text="Tradução", width=20, font=FONT,command=abrir_camera_traducao).pack(pady=5)
    tk.Button(app, text="Salvar Gestos", width=20, font=FONT,command=abrir_camera_salvar_gesto).pack(pady=5)
    tk.Button(app, text="Salvar Frases", width=20, font=FONT, command=cadastrar_frases).pack(pady=5)


def mostrar_alfabeto():
    for widget in app.winfo_children():
        widget.destroy()

    app.title("Alfabeto em Libras")

    tk.Label(app, text="Clique em uma letra para ver em Libras:", font=TITLE_FONT, bg=BG_COLOR).pack(pady=10)

    frame_letras = tk.Frame(app, bg=BG_COLOR)
    frame_letras.pack()

    frame_imagem = tk.Frame(app, bg=BG_COLOR)
    frame_imagem.pack(pady=20)
    imagem_label = tk.Label(frame_imagem, bg=BG_COLOR)
    imagem_label.pack()

    def mostrar_imagem(letra):
        caminho = os.path.join("imagens_libras", f"{letra}.png")
        if os.path.exists(caminho):
            imagem = Image.open(caminho)
            imagem = imagem.resize((150, 150))
            imagem_tk = ImageTk.PhotoImage(imagem)
            imagem_label.config(image=imagem_tk, text='')
            imagem_label.image = imagem_tk
        else:
            imagem_label.config(image='', text="Imagem não encontrada", font=FONT)

    letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i, letra in enumerate(letras):
        btn = tk.Button(frame_letras, text=letra, width=4, height=2, font=FONT,
                        command=lambda l=letra: mostrar_imagem(l))
        btn.grid(row=i // 6, column=i % 6, padx=5, pady=5)

    tk.Button(app, text="Voltar ao Menu", font=FONT, command=show_main_menu).pack(pady=10)


# 🆕 --- NOVA FUNÇÃO: Frases Simples ---
def mostrar_frases_simples():
    for widget in app.winfo_children():
        widget.destroy()

    app.title("Frases Simples em Libras")

    tk.Label(app, text="Selecione uma frase para ver em Libras:", font=TITLE_FONT, bg=BG_COLOR).pack(pady=10)

    frame_frases = tk.Frame(app, bg=BG_COLOR)
    frame_frases.pack(pady=10)

    frame_imagem = tk.Frame(app, bg=BG_COLOR)
    frame_imagem.pack(pady=20)

    imagem_label = tk.Label(frame_imagem, bg=BG_COLOR)
    imagem_label.pack()

    # Lista de frases e nomes de arquivos correspondentes
    frases = [
        ("Oi, tudo bem?", "oi_tudo_bem.png"),
        ("Eu sou surdo.", "eu_sou_surdo.png"),
        ("Meu nome é.", "meu_nome_e.png"),
        ("Qual seu nome?", "qual_seu_nome.png"),
        ("Hoje estou feliz.", "hoje_eu_feliz.png"),
        ("Prazer em conhecer você.", "prazer_em_conhecer_voce.png"),
        ("Bom dia.", "bom_dia.png"),
        ("Boa tarde.", "boa_tarde.png"),
        ("Boa noite.", "boa_noite.png"),
        ("Obrigado!", "obrigado.png")
    ]

    def mostrar_imagem(nome_arquivo):
        caminho = os.path.join("frases_libras", nome_arquivo)
        if os.path.exists(caminho):
            imagem = Image.open(caminho)
            imagem = imagem.resize((250, 250))
            imagem_tk = ImageTk.PhotoImage(imagem)
            imagem_label.config(image=imagem_tk, text='')
            imagem_label.image = imagem_tk
        else:
            imagem_label.config(image='', text="Imagem não encontrada", font=FONT, fg="red")

    # Criar um botão para cada frase
    for frase, arquivo in frases:
        btn = tk.Button(frame_frases, text=frase, width=30, font=FONT, bg=FRAME_COLOR,
                        command=lambda f=arquivo: mostrar_imagem(f))
        btn.pack(pady=4)

    tk.Button(app, text="Voltar ao Menu", font=FONT, command=show_main_menu).pack(pady=20)
# --- FIM DA NOVA FUNÇÃO ---


def login():
    username = entry_user.get().strip()
    password = entry_pass.get().strip()
    usuarios = carregar_usuarios()
    if username in usuarios and usuarios[username] == password:
        show_main_menu()
    else:
        messagebox.showerror("Login", "Usuário ou senha incorretos.")


def mostrar_cadastro():
    frame_login.pack_forget()
    frame_cadastro.pack(pady=10)


def cadastrar():
    new_user = entry_new_user.get().strip()
    new_pass = entry_new_pass.get().strip()
    usuarios = carregar_usuarios()
    if new_user in usuarios:
        messagebox.showerror("Cadastro", "Usuário já existe.")
    elif not new_user or not new_pass:
        messagebox.showerror("Cadastro", "Preencha todos os campos.")
    else:
        usuarios[new_user] = new_pass
        salvar_usuarios(usuarios)
        messagebox.showinfo("Cadastro", "Usuário cadastrado com sucesso!")
        entry_new_user.delete(0, tk.END)
        entry_new_pass.delete(0, tk.END)
        frame_cadastro.pack_forget()
        frame_login.pack(pady=10)


def voltar_login():
    frame_cadastro.pack_forget()
    frame_login.pack(pady=10)


# 🎨 Estilo
BG_COLOR = "#f5f6fa"
FRAME_COLOR = "#ffffff"
BTN_COLOR = "#e1e8ed"
FONT = ("Segoe UI", 12)
TITLE_FONT = ("Segoe UI", 16, "bold")

app = tk.Tk()
app.title("Menu de Login")
app.configure(bg=BG_COLOR)

style = ttk.Style(app)
style.theme_use("clam")
style.configure("TButton", font=FONT, background=BTN_COLOR, foreground="#222", borderwidth=0, focusthickness=3,
                focuscolor="#d1d8e0")
style.map("TButton", background=[("active", "#d1d8e0")])

# Frame de login
frame_login = tk.Frame(app, bg=FRAME_COLOR, bd=2, relief="groove")
frame_login.pack(pady=30, padx=30)
tk.Label(frame_login, text="Login", font=TITLE_FONT, bg=FRAME_COLOR).pack(pady=(10, 5))
tk.Label(frame_login, text="Usuário:", font=FONT, bg=FRAME_COLOR).pack(anchor="w", padx=10)
entry_user = tk.Entry(frame_login, font=FONT, bg=BG_COLOR, relief="flat")
entry_user.pack(fill="x", padx=10, pady=2)
tk.Label(frame_login, text="Senha:", font=FONT, bg=FRAME_COLOR).pack(anchor="w", padx=10)
entry_pass = tk.Entry(frame_login, show="*", font=FONT, bg=BG_COLOR, relief="flat")
entry_pass.pack(fill="x", padx=10, pady=2)
ttk.Button(frame_login, text="Entrar", command=login).pack(pady=10, padx=10, fill="x")
ttk.Button(frame_login, text="Não tem um login? Crie um cadastro aqui", command=mostrar_cadastro).pack(pady=(0, 10),
                                                                                                       padx=10,
                                                                                                       fill="x")

# Frame de cadastro
frame_cadastro = tk.Frame(app, bg=FRAME_COLOR, bd=2, relief="groove")
tk.Label(frame_cadastro, text="Cadastro", font=TITLE_FONT, bg=FRAME_COLOR).pack(pady=(10, 5))
tk.Label(frame_cadastro, text="Novo Usuário:", font=FONT, bg=FRAME_COLOR).pack(anchor="w", padx=10)
entry_new_user = tk.Entry(frame_cadastro, font=FONT, bg=BG_COLOR, relief="flat")
entry_new_user.pack(fill="x", padx=10, pady=2)
tk.Label(frame_cadastro, text="Nova Senha:", font=FONT, bg=FRAME_COLOR).pack(anchor="w", padx=10)
entry_new_pass = tk.Entry(frame_cadastro, show="*", font=FONT, bg=BG_COLOR, relief="flat")
entry_new_pass.pack(fill="x", padx=10, pady=2)
ttk.Button(frame_cadastro, text="Cadastrar", command=cadastrar).pack(pady=10, padx=10, fill="x")
ttk.Button(frame_cadastro, text="Voltar para o login", command=voltar_login).pack(pady=(0, 10), padx=10, fill="x")

app.mainloop()
