# -*- coding: utf-8 -*-
"""
Formatador DMR - Interface Grafica
===================================
Aplicativo de janela para formatar a base de usuarios DMR (radioid / cbridge_user)
para o schema usado no radio. Reutiliza TODA a logica de formatar_dmr.py.

- Selecione o arquivo base (ex.: cbridge_user.csv)
- Clique em "Gerar CSV", escolha onde salvar
- O CSV formatado e gravado no local escolhido

Empacotado com PyInstaller num unico .exe (nao requer Python instalado).
"""
import os
import sys
import csv
import runpy
import traceback
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime


def resource_path(rel):
    """Caminho de recurso compativel com PyInstaller (sys._MEIPASS) e execucao normal."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def processar(entrada, saida, log):
    """Executa a logica de formatar_dmr.py passando entrada/saida via argv.

    formatar_dmr.py roda no corpo do modulo lendo sys.argv[1]=ENTRADA, [2]=SAIDA.
    Reaproveitamos sem duplicar regras."""
    script = resource_path("formatar_dmr.py")
    if not os.path.exists(script):
        # fallback: ao lado do executavel
        script = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "formatar_dmr.py")

    argv_bkp = sys.argv[:]
    stdout_bkp = sys.stdout

    class _Tee:
        def write(self, s):
            if s.strip():
                log(s.rstrip("\n"))
        def flush(self):
            pass

    try:
        sys.argv = [script, entrada, saida]
        sys.stdout = _Tee()
        runpy.run_path(script, run_name="__main__")
        return True
    finally:
        sys.argv = argv_bkp
        sys.stdout = stdout_bkp


class App:
    def __init__(self, root):
        self.root = root
        self.entrada = tk.StringVar()
        root.title("Formatador de DMR ID - PP5RD")
        root.geometry("640x500")
        root.minsize(560, 400)

        tk.Label(root, text="Formatador de DMR ID", font=("Segoe UI", 14, "bold")).pack(pady=(14, 2))
        tk.Label(root, text="Converte a base do radioid (cbridge_user.csv) para uma exibicao",
                 font=("Segoe UI", 9), fg="#555").pack()
        tk.Label(root, text="confortavel na tela do radio Radtel RT-4D.",
                 font=("Segoe UI", 9), fg="#555").pack()
        dllink = tk.Label(root, text="Baixe o arquivo cbridge_user.csv em: radioid.net/database/dumps",
                          font=("Segoe UI", 9, "underline"), fg="#0a66c2", cursor="hand2")
        dllink.pack(pady=(2, 0))
        dllink.bind("<Button-1>", lambda e: webbrowser.open("https://radioid.net/database/dumps"))

        frm = tk.Frame(root)
        frm.pack(fill="x", padx=16, pady=(16, 6))
        tk.Label(frm, text="Arquivo base:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        row = tk.Frame(frm)
        row.pack(fill="x", pady=4)
        self.ent = tk.Entry(row, textvariable=self.entrada)
        self.ent.pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Selecionar...", command=self.selecionar).pack(side="left", padx=(8, 0))

        btnrow = tk.Frame(root)
        btnrow.pack(fill="x", padx=16, pady=8)
        self.btn = tk.Button(btnrow, text="Gerar CSV", font=("Segoe UI", 10, "bold"),
                             bg="#305496", fg="white", height=2, command=self.gerar)
        self.btn.pack(fill="x")

        tk.Label(root, text="Log:", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16)
        self.txt = scrolledtext.ScrolledText(root, height=11, font=("Consolas", 9))
        self.txt.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        self.log("Pronto. Selecione o arquivo base e clique em Gerar CSV.")

        # Rodape: autoria PP5RD + contato (link mailto clicavel)
        rod = tk.Frame(root)
        rod.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(rod, text="PP5RD", font=("Segoe UI", 9, "bold"), fg="#305496").pack(side="left")
        tk.Label(rod, text=" - ", font=("Segoe UI", 9), fg="#777").pack(side="left")
        link = tk.Label(rod, text="contato@pp5rd.com.br", font=("Segoe UI", 9, "underline"), fg="#0a66c2", cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open("mailto:contato@pp5rd.com.br"))

    def log(self, msg):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.root.update_idletasks()

    def selecionar(self):
        f = filedialog.askopenfilename(
            title="Selecione o arquivo base (cbridge_user)",
            filetypes=[("CSV / Texto", "*.csv *.txt"), ("Todos", "*.*")])
        if f:
            self.entrada.set(f)
            self.log("Arquivo base: " + f)

    def gerar(self):
        entrada = self.entrada.get().strip()
        if not entrada or not os.path.exists(entrada):
            messagebox.showwarning("Atencao", "Selecione um arquivo base valido.")
            return
        sugerido = datetime.now().strftime("%Y%m%d%H%M") + ".csv"
        saida = filedialog.asksaveasfilename(
            title="Salvar CSV formatado como...",
            defaultextension=".csv",
            initialfile=sugerido,
            filetypes=[("CSV", "*.csv")])
        if not saida:
            return
        self.btn.config(state="disabled", text="Processando...")
        threading.Thread(target=self._run, args=(entrada, saida), daemon=True).start()

    def _run(self, entrada, saida):
        try:
            self.log("Processando, aguarde...")
            processar(entrada, saida, self.log)
            # conta linhas da saida
            n = 0
            with open(saida, encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1
            self.log("")
            self.log("Concluido! %d registros gravados em:" % n)
            self.log(saida)
            messagebox.showinfo("Concluido", "CSV gerado com sucesso!\n\n%d registros\n%s" % (n, saida))
        except Exception as e:
            self.log("ERRO: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", "Falha ao gerar o CSV:\n%s" % e)
        finally:
            self.btn.config(state="normal", text="Gerar CSV")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()


