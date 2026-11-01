"""Regera os graficos 5 e 6 do Fragmentos Lab com acentuacao completa e nomes de cenario do artigo.
Usa os mesmos dados do ensaios.csv dentro do ZIP v0.5.0 e o mesmo estilo do tools/build_article.py."""
import csv
import io
import sys
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ZIP, OUTDIR = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(ZIP)
rows = list(csv.DictReader(io.StringIO(z.read("fragmentos-lab/reports/article/ensaios.csv").decode())))

models = ["qwen2.5:1.5b", "qwen2.5:0.5b", "qwen2.5:3b", "llama3.2:1b", "llama3.2:3b", "gemma3:270m", "gemma3:1b", "gemma3:4b",
          "smollm2:135m", "smollm2:360m", "smollm2:1.7b", "granite3.3:2b", "phi3.5:3.8b", "qwen3:0.6b", "qwen3:1.7b", "deepseek-r1:1.5b"]
cases = ["benign", "injection_observe", "mismatch_observe", "mismatch_enforce", "authorized", "unilateral", "silent"]
assert {r["model"] for r in rows} == set(models), "modelos do CSV diferem da lista"
assert {r["case"] for r in rows} == set(cases), "cenarios do CSV diferem da lista"

valids = [sum(1 for r in rows if r["model"] == m and r["status"] == "valid") for m in models]
err = [sum(1 for r in rows if r["model"] == m and r["status"] != "valid") for m in models]
missing = [14 - v - e for v, e in zip(valids, err)]
print("validos", sum(valids), "erros", sum(err), "sem resultado", sum(missing))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": "white"})

labels = models
fig, ax = plt.subplots(figsize=(9, 7.5))
y = np.arange(len(labels))
ax.barh(y, valids, color="#168b82", label="Resultado válido")
ax.barh(y, err, left=valids, color="#ce644f", label="Erro de execução")
ax.barh(y, missing, left=np.array(valids) + err, color="#dce3e8", label="Sem resultado concluído")
ax.set_yticks(y, labels)
ax.invert_yaxis()
ax.set_xlim(0, 14)
ax.set_xlabel("Ensaios por modelo (14 previstos)")
ax.legend(loc="upper center", bbox_to_anchor=(.5, -.1), ncol=3, fontsize=8)
ax.set_title("Compatibilidade com o protocolo integrado-v2", loc="left", fontweight="bold")
ax.grid(axis="x", alpha=.18)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUTDIR + "/05-compatibilidade.png", dpi=220, bbox_inches="tight")
plt.close(fig)

grid = np.full((len(labels), len(cases)), np.nan)
cell = {}
for i, m in enumerate(labels):
    for j, c in enumerate(cases):
        sub = [r for r in rows if r["model"] == m and r["case"] == c and r["status"] == "valid"]
        rec = sum(1 for r in sub if r["reconstructed"] == "True")
        cell[(i, j)] = (rec, len(sub))
        if sub:
            grid[i, j] = rec / len(sub)

fig, ax = plt.subplots(figsize=(11, 8.4))
cmap = plt.get_cmap("YlGnBu").copy()
cmap.set_bad("#e2e7eb")
ax.imshow(grid, vmin=0, vmax=1, cmap=cmap, aspect="auto")
ax.set_yticks(np.arange(len(labels)), labels, fontsize=12.5)
ax.set_xticks(np.arange(len(cases)), ["Controle", "Injeção", "Conflito sem\nbloqueio", "Conflito com\nbloqueio", "Fluxo\nautorizado", "Um só\npedaço", "Juntar sem\npublicar"], fontsize=11.5)
for i, m in enumerate(labels):
    for j, c in enumerate(cases):
        rec, val = cell[(i, j)]
        text = f"{rec}/{val}" if val else "ERR"
        ax.text(j, i, text, ha="center", va="center", fontsize=12.5, color="white" if not np.isnan(grid[i, j]) and grid[i, j] > .6 else "#193548")
ax.set_xlabel("Nomes no código: benign, injection_observe, mismatch_observe, mismatch_enforce, authorized, unilateral, silent.\nERR significa nenhum ensaio válido, e não zero violações.", fontsize=9.5, labelpad=12)
ax.set_title("Reconstruções / ensaios válidos, sem inferência estatística", loc="left", fontweight="bold", fontsize=14, pad=16)
fig.tight_layout()
fig.savefig(OUTDIR + "/06-reconstrucoes.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# conferencia contra os numeros do artigo
tot = {c: (sum(cell[(i, j)][0] for i in range(len(labels))), sum(cell[(i, j)][1] for i in range(len(labels)))) for j, c in enumerate(cases)}
print(tot)
