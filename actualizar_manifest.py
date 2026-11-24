#!/usr/bin/env python3
"""Actualiza cursos/manifest.json a partir de los JSON de cursos/.

- Añade los cursos cuyo archivo todavía no está en el catálogo (id, título,
  descripción e imagen se copian del propio JSON).
- Rellena «numLecciones» y «numEjercicios». La app los muestra en el catálogo
  («1030 lecciones · 984 ejercicios»); si faltan, no muestra nada.

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


def cargar_json(ruta: Path):
    raw = ruta.read_text(encoding="utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        lineas = raw.splitlines()
        i = e.lineno - 1
        trozo = "\n".join(
            f"{n + 1:5}| {lineas[n]}"
            for n in range(max(0, i - 3), min(len(lineas), i + 4))
        )
        raise SystemExit(
            f"JSON inválido en {ruta} (línea {e.lineno}, columna {e.colno}): {e.msg}\n"
            "Casi siempre falta una coma entre dos cursos, p. ej.:\n"
            '      "numEjercicios": 325\n'
            "    },          ← esta coma\n"
            "    {\n"
            f"{trozo}"
        ) from e


def agregar_cursos_nuevos(cursos):
    """Añade al catálogo los JSON de cursos/ que aún no tienen entrada."""
    conocidos = {c.get("bundleUrl") for c in cursos}
    ids = {c.get("id") for c in cursos}
    carpeta = RAIZ / "cursos"
    agregados = 0
    for ruta in sorted(carpeta.glob("*.json")):
        if ruta.name == "manifest.json":
            continue
        rel = ruta.relative_to(RAIZ).as_posix()
        if rel in conocidos:
            continue
        curso = cargar_json(ruta)
        if not isinstance(curso, dict) or "lecciones" not in curso:
            print(f"AVISO: {rel} no parece un curso, lo omito.")
            continue
        cid = curso.get("id")
        if not cid:
            print(f"AVISO: {rel} no tiene id, lo omito.")
            continue
        if cid in ids:
            print(f"AVISO: {rel} repite el id {cid}, lo omito.")
            continue
        n_lec, n_ej = contar(curso)
        cursos.append({
            "id": cid,
            "titulo": curso.get("titulo") or ruta.stem,
            "descripcion": curso.get("descripcion") or "",
            "imagenUrl": curso.get("imagenUrl") or "",
            "version": 1,
            "bundleUrl": rel,
            "numLecciones": n_lec,
            "numEjercicios": n_ej,
        })
        conocidos.add(rel)
        ids.add(cid)
        agregados += 1
        print(f"NUEVO  {n_lec:5} lecciones · {n_ej:5} ejercicios · {curso.get('titulo')} ({rel})")
    return agregados


def main():
    manifest = cargar_json(MANIFEST)
    cursos = manifest["cursos"] if isinstance(manifest, dict) else manifest
    cambios = agregar_cursos_nuevos(cursos)
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
    print(f"manifest.json actualizado ({cambios} cambio{'s' if cambios != 1 else ''}).")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
