#!/usr/bin/env python3
"""Rellena en cursos/manifest.json cuántas lecciones y ejercicios tiene cada
curso («numLecciones», «numEjercicios»), contándolos en su JSON. La app los
muestra en el catálogo («1030 lecciones · 984 ejercicios»); si faltan, no
muestra nada.

Ejercicios = diagramas para jugar (MOVIMIENTO), partidas contra la máquina
(VSPC) y preguntas (QUIZ) con al menos 2 opciones y la respuesta entre ellas.

Uso (desde la raíz del repositorio, después de añadir o cambiar cursos):
    python actualizar_manifest.py
"""
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MANIFEST = RAIZ / "cursos" / "manifest.json"


def es_quiz_valido(s):
    opciones = s.get("opciones")
    correcta = str(s.get("respuestaCorrecta") or "").strip()
    return (s.get("tipo") == "QUIZ" and isinstance(opciones, list)
            and len(opciones) >= 2 and correcta in [str(o).strip() for o in opciones])


def contar(curso):
    lecciones = curso.get("lecciones") or []
    ejercicios = sum(1 for l in lecciones for s in (l.get("segmentos") or [])
                     if s.get("tipo") in ("MOVIMIENTO", "VSPC") or es_quiz_valido(s))
    return len(lecciones), ejercicios


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    cursos = manifest["cursos"] if isinstance(manifest, dict) else manifest
    cambios = 0
    for c in cursos:
        ruta = RAIZ / c.get("bundleUrl", "")
        if not ruta.is_file():
            print(f"AVISO: {c.get('titulo')}: no encuentro {c.get('bundleUrl')}")
            continue
        n_lec, n_ej = contar(json.loads(ruta.read_text(encoding="utf-8-sig")))
        if (c.get("numLecciones"), c.get("numEjercicios")) != (n_lec, n_ej):
            c["numLecciones"], c["numEjercicios"] = n_lec, n_ej
            cambios += 1
        print(f"{n_lec:5} lecciones · {n_ej:5} ejercicios · {c.get('titulo')}")
    if not cambios:
        print("Sin cambios.")
        return
    if isinstance(manifest, dict) and "actualizado" in manifest:
        manifest["actualizado"] = date.today().isoformat()
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"manifest.json actualizado ({cambios} cursos).")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
