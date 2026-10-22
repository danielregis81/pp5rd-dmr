// Formatador DMR - PP5RD - app web via Pyodide
// Reutiliza o formatar_dmr.py (mesma logica do desktop) rodando no navegador.

const $ = (id) => document.getElementById(id);
const logEl = $("log");
const statusEl = $("status");
const btn = $("gerar");
const fileEl = $("arquivo");

let pyodide = null;
let scriptReady = false;
let currentLang = "pt";

// --- i18n: textos da interface (PT padrao, EN opcional) ---
const I18N = {
  pt: {
    uiLangLabel: "Idioma / Language:",
    title: "Formatador de DMR ID",
    sub1: 'Converte a base do radioid (<b>cbridge_user.csv</b>) para uma exibicao confortavel na tela do radio <b>Radtel RT-4D</b>.',
    sub2: 'Baixe o arquivo <b>cbridge_user.csv</b> em: <a href="https://radioid.net/database/dumps" target="_blank" rel="noopener">radioid.net/database/dumps</a>',
    fileLabel: "Arquivo base (cbridge_user.csv):",
    countryLangLabel: "Idioma dos nomes de paises:",
    optPt: "Portugues (ex.: Alemanha, Franca)",
    optEn: "English (e.g. Germany, France)",
    btnLoading: "Carregando motor...",
    btnReady: "Gerar CSV",
    btnSelectFile: "Selecione o arquivo",
    btnProcessing: "Processando...",
    statusInit: "Inicializando o processador (primeira carga pode demorar)...",
    statusDownloading: "Baixando o motor Python (Pyodide)...",
    statusInstalling: "Instalando dependencias (unidecode)...",
    statusLoadingRules: "Carregando regras e referencia de regioes...",
    statusReady: '<span class="ok">Pronto!</span> Selecione o cbridge_user.csv e clique em Gerar.',
    statusDone: (n) => '<span class="ok">CSV gerado!</span> ' + n + ' registros. O download iniciou automaticamente.',
    logReady: "Motor carregado. Pronto para processar.",
    logReading: "Lendo arquivo...",
    logProcessing: "Processando (pode levar alguns segundos para bases grandes)...",
    logDone: (n) => "Concluido! " + n + " registros gerados.",
    warnFile: "Selecione um arquivo base valido.",
    errInit: "Erro ao inicializar: ",
    errProcess: "Erro ao processar: ",
    winPrompt: "Prefere a versao para Windows?",
    winLink: "Baixar o aplicativo (.exe)",
  },
  en: {
    uiLangLabel: "Idioma / Language:",
    title: "DMR ID Formatter",
    sub1: 'Converts the radioid database (<b>cbridge_user.csv</b>) for a comfortable display on the <b>Radtel RT-4D</b> radio screen.',
    sub2: 'Download <b>cbridge_user.csv</b> at: <a href="https://radioid.net/database/dumps" target="_blank" rel="noopener">radioid.net/database/dumps</a>',
    fileLabel: "Base file (cbridge_user.csv):",
    countryLangLabel: "Country names language:",
    optPt: "Portugues (e.g. Alemanha, Franca)",
    optEn: "English (e.g. Germany, France)",
    btnLoading: "Loading engine...",
    btnReady: "Generate CSV",
    btnSelectFile: "Select a file",
    btnProcessing: "Processing...",
    statusInit: "Initializing the processor (first load may take a while)...",
    statusDownloading: "Downloading the Python engine (Pyodide)...",
    statusInstalling: "Installing dependencies (unidecode)...",
    statusLoadingRules: "Loading rules and region reference...",
    statusReady: '<span class="ok">Ready!</span> Select cbridge_user.csv and click Generate.',
    statusDone: (n) => '<span class="ok">CSV generated!</span> ' + n + ' records. The download started automatically.',
    logReady: "Engine loaded. Ready to process.",
    logReading: "Reading file...",
    logProcessing: "Processing (may take a few seconds for large files)...",
    logDone: (n) => "Done! " + n + " records generated.",
    warnFile: "Please select a valid base file.",
    errInit: "Initialization error: ",
    errProcess: "Processing error: ",
    winPrompt: "Prefer the Windows version?",
    winLink: "Download the app (.exe)",
  },
};

function t(key) { return (I18N[currentLang] && I18N[currentLang][key]) || I18N.pt[key]; }

function applyLang(lang) {
  currentLang = (lang === "en") ? "en" : "pt";
  document.documentElement.lang = (currentLang === "en") ? "en" : "pt-br";
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const v = t(el.getAttribute("data-i18n"));
    if (typeof v === "string") el.innerHTML = v;
  });
  // botao: depende do estado atual
  if (!scriptReady) btn.textContent = t("btnLoading");
  else btn.textContent = (fileEl.files.length > 0) ? t("btnReady") : t("btnSelectFile");
  // se o motor ja esta pronto e nada foi processado ainda, atualiza status e
  // a mensagem inicial do log para o idioma recem-selecionado.
  if (scriptReady && !processouAlgo) {
    statusEl.innerHTML = t("statusReady");
    logEl.textContent = "";
    log(t("logReady"));
  }
}

let processouAlgo = false;

function log(msg) {
  logEl.textContent += msg + "\n";
  logEl.scrollTop = logEl.scrollHeight;
}

async function init() {
  try {
    statusEl.textContent = t("statusDownloading");
    pyodide = await loadPyodide();

    statusEl.textContent = t("statusInstalling");
    await pyodide.loadPackage("micropip");
    await pyodide.runPythonAsync(`
import micropip
await micropip.install("Unidecode")
`);

    statusEl.textContent = t("statusLoadingRules");
    // baixa o script de formatacao e a referencia, grava no FS virtual do Pyodide
    const [scriptTxt, refTxt] = await Promise.all([
      fetch("formatar_dmr.py?v6").then(r => r.text()),
      fetch("ref/regioes_ref.csv?v6").then(r => r.text()),
    ]);

    // cria a estrutura de pastas que o script espera: ./ref/regioes_ref.csv
    pyodide.FS.mkdirTree("/app/ref");
    pyodide.FS.writeFile("/app/formatar_dmr.py", scriptTxt);
    pyodide.FS.writeFile("/app/ref/regioes_ref.csv", refTxt);

    scriptReady = true;
    statusEl.innerHTML = t("statusReady");
    log(t("logReady"));
    atualizaBotao();
  } catch (e) {
    statusEl.textContent = t("errInit") + e;
    log("ERRO init: " + e);
  }
}

function atualizaBotao() {
  if (scriptReady && fileEl.files.length > 0) {
    btn.disabled = false;
    btn.textContent = t("btnReady");
  } else if (scriptReady) {
    btn.disabled = true;
    btn.textContent = t("btnSelectFile");
  }
}

fileEl.addEventListener("change", atualizaBotao);

// seletor de idioma da interface
$("uiLang").addEventListener("change", (e) => applyLang(e.target.value));

btn.addEventListener("click", async () => {
  if (!scriptReady || fileEl.files.length === 0) return;
  processouAlgo = true;
  btn.disabled = true;
  btn.textContent = t("btnProcessing");
  log(t("logReading"));
  try {
    const file = fileEl.files[0];
    const texto = await file.text();

    // grava a base no FS virtual
    pyodide.FS.writeFile("/app/entrada.csv", texto);

    log(t("logProcessing"));
    // idioma unificado: a mesma selecao da interface controla a saida do arquivo
    const idioma = currentLang;
    pyodide.globals.set("_idioma_sel", idioma);
    // roda o formatar_dmr.py como: python formatar_dmr.py entrada.csv saida.csv <idioma>
    await pyodide.runPythonAsync(`
import os, sys, runpy
os.chdir("/app")
sys.argv = ["formatar_dmr.py", "/app/entrada.csv", "/app/saida.csv", _idioma_sel]
runpy.run_path("/app/formatar_dmr.py", run_name="__main__")
`);

    const saida = pyodide.FS.readFile("/app/saida.csv", { encoding: "utf8" });
    const nLinhas = saida.split("\n").filter(l => l.trim()).length - 1;
    log(t("logDone")(nLinhas));

    // oferece download
    const blob = new Blob([saida], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const ts = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 12);
    a.href = url;
    a.download = ts + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    statusEl.innerHTML = t("statusDone")(nLinhas);
  } catch (e) {
    log("ERRO: " + e);
    statusEl.textContent = t("errProcess") + e;
  } finally {
    btn.disabled = false;
    btn.textContent = t("btnReady");
  }
});

// aplica idioma inicial (PT) e inicia
applyLang("pt");
init();





