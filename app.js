// Formatador DMR - PP5RD - app web via Pyodide
// Reutiliza o formatar_dmr.py (mesma logica do desktop) rodando no navegador.

const $ = (id) => document.getElementById(id);
const logEl = $("log");
const statusEl = $("status");
const btn = $("gerar");
const fileEl = $("arquivo");

let pyodide = null;
let scriptReady = false;

function log(msg) {
  logEl.textContent += msg + "\n";
  logEl.scrollTop = logEl.scrollHeight;
}

async function init() {
  try {
    statusEl.textContent = "Baixando o motor Python (Pyodide)...";
    pyodide = await loadPyodide();

    statusEl.textContent = "Instalando dependencias (unidecode)...";
    await pyodide.loadPackage("micropip");
    await pyodide.runPythonAsync(`
import micropip
await micropip.install("Unidecode")
`);

    statusEl.textContent = "Carregando regras e referencia de regioes...";
    // baixa o script de formatacao e a referencia, grava no FS virtual do Pyodide
    const [scriptTxt, refTxt] = await Promise.all([
      fetch("formatar_dmr.py").then(r => r.text()),
      fetch("ref/regioes_ref.csv").then(r => r.text()),
    ]);

    // cria a estrutura de pastas que o script espera: ./ref/regioes_ref.csv
    pyodide.FS.mkdirTree("/app/ref");
    pyodide.FS.writeFile("/app/formatar_dmr.py", scriptTxt);
    pyodide.FS.writeFile("/app/ref/regioes_ref.csv", refTxt);

    scriptReady = true;
    statusEl.innerHTML = '<span class="ok">Pronto!</span> Selecione o cbridge_user.csv e clique em Gerar.';
    log("Motor carregado. Pronto para processar.");
    atualizaBotao();
  } catch (e) {
    statusEl.textContent = "Erro ao inicializar: " + e;
    log("ERRO init: " + e);
  }
}

function atualizaBotao() {
  if (scriptReady && fileEl.files.length > 0) {
    btn.disabled = false;
    btn.textContent = "Gerar CSV";
  } else if (scriptReady) {
    btn.disabled = true;
    btn.textContent = "Selecione o arquivo";
  }
}

fileEl.addEventListener("change", atualizaBotao);

btn.addEventListener("click", async () => {
  if (!scriptReady || fileEl.files.length === 0) return;
  btn.disabled = true;
  btn.textContent = "Processando...";
  log("Lendo arquivo...");
  try {
    const file = fileEl.files[0];
    const texto = await file.text();

    // grava a base no FS virtual
    pyodide.FS.writeFile("/app/entrada.csv", texto);

    log("Processando (pode levar alguns segundos para bases grandes)...");
    // roda o formatar_dmr.py como se fosse: python formatar_dmr.py entrada.csv saida.csv
    await pyodide.runPythonAsync(`
import os, sys, runpy
os.chdir("/app")
sys.argv = ["formatar_dmr.py", "/app/entrada.csv", "/app/saida.csv"]
runpy.run_path("/app/formatar_dmr.py", run_name="__main__")
`);

    const saida = pyodide.FS.readFile("/app/saida.csv", { encoding: "utf8" });
    const nLinhas = saida.split("\n").filter(l => l.trim()).length - 1;
    log("Concluido! " + nLinhas + " registros gerados.");

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

    statusEl.innerHTML = '<span class="ok">CSV gerado!</span> ' + nLinhas + ' registros. O download iniciou automaticamente.';
  } catch (e) {
    log("ERRO: " + e);
    statusEl.textContent = "Erro ao processar: " + e;
  } finally {
    btn.disabled = false;
    btn.textContent = "Gerar CSV";
  }
});

init();

