# -*- coding: utf-8 -*-
"""
Formatador de DMR ID - Interface Grafica (PP5RD)
================================================
Formata a base de usuarios DMR (radioid / cbridge_user.csv) para exibicao
confortavel na tela do radio Radtel RT-4D. Reutiliza a logica de formatar_dmr.py.

- Idioma da interface (PT/EN) e idioma dos nomes de paises (PT/EN) selecionaveis.
- Empacotado com PyInstaller num unico .exe (nao requer Python instalado).
"""
import os
import sys
import runpy
import traceback
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


# --- i18n da interface ---
I18N = {
    "pt": {
        "title": "Formatador de DMR ID",
        "sub1": "Converte a base do radioid (cbridge_user.csv) para uma exibicao",
        "sub2": "confortavel na tela do radio Radtel RT-4D.",
        "dllink": "Baixe o arquivo cbridge_user.csv em: radioid.net/database/dumps",
        "uiLang": "Idioma / Language:",
        "fileLabel": "Arquivo base:",
        "selectBtn": "Selecionar...",
        "countryLang": "Idioma dos nomes de paises:",
        "genBtn": "Gerar CSV",
        "processing": "Processando...",
        "logReady": "Pronto. Selecione o arquivo base e clique em Gerar CSV.",
        "logFile": "Arquivo base: ",
        "logProcessing": "Processando, aguarde...",
        "logDone": "Concluido! %d registros gravados em:",
        "warnFile": "Selecione um arquivo base valido.",
        "warnTitle": "Atencao",
        "saveTitle": "Salvar CSV formatado como...",
        "openTitle": "Selecione o arquivo base (cbridge_user)",
        "doneTitle": "Concluido",
        "doneMsg": "CSV gerado com sucesso!\n\n%d registros\n%s",
        "errTitle": "Erro",
        "errMsg": "Falha ao gerar o CSV:\n%s",
        "logLabel": "Log:",
    },
    "en": {
        "title": "DMR ID Formatter",
        "sub1": "Converts the radioid database (cbridge_user.csv) for a comfortable",
        "sub2": "display on the Radtel RT-4D radio screen.",
        "dllink": "Download cbridge_user.csv at: radioid.net/database/dumps",
        "uiLang": "Idioma / Language:",
        "fileLabel": "Base file:",
        "selectBtn": "Select...",
        "countryLang": "Country names language:",
        "genBtn": "Generate CSV",
        "processing": "Processing...",
        "logReady": "Ready. Select the base file and click Generate CSV.",
        "logFile": "Base file: ",
        "logProcessing": "Processing, please wait...",
        "logDone": "Done! %d records written to:",
        "warnFile": "Please select a valid base file.",
        "warnTitle": "Warning",
        "saveTitle": "Save formatted CSV as...",
        "openTitle": "Select the base file (cbridge_user)",
        "doneTitle": "Done",
        "doneMsg": "CSV generated successfully!\n\n%d records\n%s",
        "errTitle": "Error",
        "errMsg": "Failed to generate CSV:\n%s",
        "logLabel": "Log:",
    },
}


def processar(entrada, saida, idioma_pais, log):
    """Roda formatar_dmr.py via argv: entrada, saida e idioma dos paises (pt/en)."""
    script = resource_path("formatar_dmr.py")
    if not os.path.exists(script):
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
        sys.argv = [script, entrada, saida, idioma_pais]
        sys.stdout = _Tee()
        runpy.run_path(script, run_name="__main__")
        return True
    finally:
        sys.argv = argv_bkp
        sys.stdout = stdout_bkp


class App:
    def __init__(self, root):
        self.root = root
        self.lang = "pt"
        self.entrada = tk.StringVar()
        self.ui_lang = tk.StringVar(value="pt")
        self.pais_lang = tk.StringVar(value="pt")
        root.title("Formatador de DMR ID - PP5RD")
        root.geometry("660x560")
        root.minsize(560, 460)

        # seletor de idioma da UI (topo direito)
        toprow = tk.Frame(root)
        toprow.pack(fill="x", padx=16, pady=(8, 0))
        self.lbl_uilang = tk.Label(toprow, text="", font=("Segoe UI", 9))
        self.lbl_uilang.pack(side="right")
        self.cb_uilang = ttk.Combobox(toprow, width=12, state="readonly",
                                      values=["Portugues", "English"], textvariable=tk.StringVar())
        self.cb_uilang.current(0)
        self.cb_uilang.pack(side="right", padx=(0, 6))
        self.cb_uilang.bind("<<ComboboxSelected>>", self._troca_ui_lang)

        self.lbl_title = tk.Label(root, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_title.pack(pady=(6, 2))
        self.lbl_sub1 = tk.Label(root, text="", font=("Segoe UI", 9), fg="#555")
        self.lbl_sub1.pack()
        self.lbl_sub2 = tk.Label(root, text="", font=("Segoe UI", 9), fg="#555")
        self.lbl_sub2.pack()
        self.lbl_dl = tk.Label(root, text="", font=("Segoe UI", 9, "underline"), fg="#0a66c2", cursor="hand2")
        self.lbl_dl.pack(pady=(2, 0))
        self.lbl_dl.bind("<Button-1>", lambda e: webbrowser.open("https://radioid.net/database/dumps"))

        frm = tk.Frame(root)
        frm.pack(fill="x", padx=16, pady=(16, 6))
        self.lbl_file = tk.Label(frm, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_file.pack(anchor="w")
        row = tk.Frame(frm)
        row.pack(fill="x", pady=4)
        self.ent = tk.Entry(row, textvariable=self.entrada)
        self.ent.pack(side="left", fill="x", expand=True)
        self.btn_sel = tk.Button(row, text="", command=self.selecionar)
        self.btn_sel.pack(side="left", padx=(8, 0))

        # seletor de idioma dos paises
        frm2 = tk.Frame(root)
        frm2.pack(fill="x", padx=16, pady=(4, 6))
        self.lbl_paislang = tk.Label(frm2, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_paislang.pack(anchor="w")
        self.cb_paislang = ttk.Combobox(frm2, state="readonly",
                                        values=["Portugues (Alemanha, Franca)", "English (Germany, France)"])
        self.cb_paislang.current(0)
        self.cb_paislang.pack(fill="x", pady=2)

        btnrow = tk.Frame(root)
        btnrow.pack(fill="x", padx=16, pady=8)
        self.btn = tk.Button(btnrow, text="", font=("Segoe UI", 10, "bold"),
                             bg="#305496", fg="white", height=2, command=self.gerar)
        self.btn.pack(fill="x")

        self.lbl_log = tk.Label(root, text="", font=("Segoe UI", 9, "bold"))
        self.lbl_log.pack(anchor="w", padx=16)
        self.txt = scrolledtext.ScrolledText(root, height=11, font=("Consolas", 9))
        self.txt.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        rod = tk.Frame(root)
        rod.pack(fill="x", padx=16, pady=(0, 10))
        tk.Label(rod, text="PP5RD", font=("Segoe UI", 9, "bold"), fg="#305496").pack(side="left")
        tk.Label(rod, text=" - ", font=("Segoe UI", 9), fg="#777").pack(side="left")
        link = tk.Label(rod, text="contato@pp5rd.com.br", font=("Segoe UI", 9, "underline"), fg="#0a66c2", cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open("mailto:contato@pp5rd.com.br"))

        self._aplica_textos()
        self.log(self._t("logReady"))

    def _t(self, key):
        return I18N[self.lang][key]

    def _aplica_textos(self):
        self.lbl_uilang.config(text=self._t("uiLang"))
        self.lbl_title.config(text=self._t("title"))
        self.lbl_sub1.config(text=self._t("sub1"))
        self.lbl_sub2.config(text=self._t("sub2"))
        self.lbl_dl.config(text=self._t("dllink"))
        self.lbl_file.config(text=self._t("fileLabel"))
        self.btn_sel.config(text=self._t("selectBtn"))
        self.lbl_paislang.config(text=self._t("countryLang"))
        self.btn.config(text=self._t("genBtn"))
        self.lbl_log.config(text=self._t("logLabel"))

    def _troca_ui_lang(self, event=None):
        self.lang = "en" if self.cb_uilang.current() == 1 else "pt"
        self._aplica_textos()

    def log(self, msg):
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.root.update_idletasks()

    def selecionar(self):
        f = filedialog.askopenfilename(
            title=self._t("openTitle"),
            filetypes=[("CSV / Texto", "*.csv *.txt"), ("Todos", "*.*")])
        if f:
            self.entrada.set(f)
            self.log(self._t("logFile") + f)

    def gerar(self):
        entrada = self.entrada.get().strip()
        if not entrada or not os.path.exists(entrada):
            messagebox.showwarning(self._t("warnTitle"), self._t("warnFile"))
            return
        sugerido = datetime.now().strftime("%Y%m%d%H%M") + ".csv"
        saida = filedialog.asksaveasfilename(
            title=self._t("saveTitle"), defaultextension=".csv",
            initialfile=sugerido, filetypes=[("CSV", "*.csv")])
        if not saida:
            return
        idioma_pais = "en" if self.cb_paislang.current() == 1 else "pt"
        self.btn.config(state="disabled", text=self._t("processing"))
        threading.Thread(target=self._run, args=(entrada, saida, idioma_pais), daemon=True).start()

    def _run(self, entrada, saida, idioma_pais):
        try:
            self.log(self._t("logProcessing"))
            processar(entrada, saida, idioma_pais, self.log)
            n = 0
            with open(saida, encoding="utf-8") as fh:
                n = sum(1 for _ in fh) - 1
            self.log("")
            self.log(self._t("logDone") % n)
            self.log(saida)
            messagebox.showinfo(self._t("doneTitle"), self._t("doneMsg") % (n, saida))
        except Exception as e:
            self.log("ERRO: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror(self._t("errTitle"), self._t("errMsg") % e)
        finally:
            self.btn.config(state="normal", text=self._t("genBtn"))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
