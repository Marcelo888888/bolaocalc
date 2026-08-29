#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Confere se o BolaoCalc esta publicado por inteiro, em vez de confiar na memoria.

Nasceu em 2026-08-28: as versoes v37, v38 e v39 foram publicadas e NENHUMA chegou
a loja, porque o app tem varias instalacoes e so o GitHub Pages vinha sendo
atualizado. O badge e o service worker tambem ja sairam de sincronia (badge v31
com SW v36), e a doc vendorizada ficou 227 linhas atras da fonte.

Uso:
    python verificar_publicacao.py           # tudo, inclusive os servidores
    python verificar_publicacao.py --local   # so o que esta em disco (sem rede)

Sai com codigo 1 se algo estiver fora de sincronia.

Caminhos usam barra normal de proposito: o Windows aceita, e barra invertida em
string ja corrompeu esta lista uma vez ("\\b" virou backspace), fazendo o script
pular todas as copias e ainda assim dizer "tudo publicado".
"""
import hashlib
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

# A midia de instalacao leva so o runtime (nao tem doc, por desenho). A copia
# servida pelo SistLCA leva a doc tambem, porque um agente lendo por la — a ASUS
# nao alcanca este repositorio — responde com o que estiver escrito nela.
RUNTIME = ["index.html", "service-worker.js"]
COM_DOC = RUNTIME + ["CLAUDE.md", "README.md"]

COPIAS = [
    ("C:/dev/Sist_Lca/bolaocalc", COM_DOC),
    ("C:/dev/Sist_Lca/_pendriveB/codigo/bolaocalc", RUNTIME),
    ("C:/dev/_LCA_INSTALL_LOCAL_B/codigo/bolaocalc", RUNTIME),
    ("C:/dev/LCA_INSTALL_copia_pendrive/codigo/bolaocalc", RUNTIME),
]

SERVIDORES = [
    ("GitHub Pages", "https://marcelo888888.github.io/bolaocalc/service-worker.js"),
    ("Loja (ASUS)", "http://100.91.143.80:8000/bolaocalc/service-worker.js"),
    ("Local A", "http://192.168.0.12:8000/bolaocalc/service-worker.js"),
]

falhas = []
avisos = []


def ler(caminho):
    with open(caminho, "rb") as f:
        return f.read()


def versao_sw(texto):
    m = re.search(r"bolaocalc-v(\d+)", texto)
    return m.group(1) if m else None


def versao_badge(texto):
    m = re.search(r'id="appVersion">v(\d+)<', texto)
    return m.group(1) if m else None


def checar_versao_interna():
    """O badge e o CACHE_NAME sobem juntos: o badge e' como se confere no celular."""
    sw = ler(os.path.join(RAIZ, "service-worker.js")).decode("utf-8", "replace")
    html = ler(os.path.join(RAIZ, "index.html")).decode("utf-8", "replace")
    v_sw, v_badge = versao_sw(sw), versao_badge(html)
    if not v_sw or not v_badge:
        falhas.append("nao consegui ler a versao (SW=%s, badge=%s)" % (v_sw, v_badge))
        return None
    if v_sw != v_badge:
        falhas.append("service-worker em v%s mas o badge diz v%s — sobem juntos" % (v_sw, v_badge))
        return None
    print("  OK  versao interna consistente: v%s" % v_sw)
    return v_sw


def checar_copias():
    for copia, esperados in COPIAS:
        if not os.path.isdir(copia):
            # Falha, nao aviso: ou o caminho aqui esta errado, ou a instalacao
            # sumiu. Nos dois casos e' errado dizer que esta tudo publicado.
            falhas.append("copia nao encontrada: %s" % copia)
            continue
        difs = []
        for nome in esperados:
            destino = os.path.join(copia, nome)
            if not os.path.exists(destino):
                difs.append(nome + " (faltando)")
                continue
            # CRLF vs LF nao e' divergencia de conteudo
            a = ler(os.path.join(RAIZ, nome)).replace(b"\r\n", b"\n")
            b = ler(destino).replace(b"\r\n", b"\n")
            if hashlib.sha256(a).digest() != hashlib.sha256(b).digest():
                difs.append(nome)
        if difs:
            falhas.append("copia desatualizada: %s -> %s" % (copia, ", ".join(difs)))
        else:
            print("  OK  copia em dia: %s" % copia)


def checar_servidores(esperada):
    from urllib.request import urlopen
    for nome, url in SERVIDORES:
        try:
            texto = urlopen(url, timeout=10).read().decode("utf-8", "replace")
        except Exception as e:
            # Servidor fora do ar nao e' versao errada — mas tambem nao e' prova
            # de nada, entao fica registrado como nao verificado.
            avisos.append("%s NAO VERIFICADO: nao respondeu (%s)" % (nome, e.__class__.__name__))
            continue
        v = versao_sw(texto)
        if v != esperada:
            falhas.append("%s esta servindo v%s, esperado v%s" % (nome, v, esperada))
        else:
            print("  OK  %s servindo v%s" % (nome, v))


def main():
    so_local = "--local" in sys.argv
    print("Conferindo publicacao do BolaoCalc\n")
    versao = checar_versao_interna()
    checar_copias()
    if versao and not so_local:
        checar_servidores(versao)

    print("")
    for a in avisos:
        print("  !   %s" % a)
    if falhas:
        for f in falhas:
            print("  X   %s" % f)
        print("\n%d ponto(s) fora de sincronia. Ver o checklist no CLAUDE.md." % len(falhas))
        return 1
    if avisos:
        print("Nada fora de sincronia — mas veja os nao verificados acima.")
    else:
        print("Tudo publicado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
