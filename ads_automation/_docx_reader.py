"""Minimal .docx reader using stdlib only — no external dependencies.

.docx files are ZIP archives. Paragraphs and tables live in word/document.xml.
This module exposes the same Document / paragraphs / tables / cells API that
python-docx provides, covering exactly what parser.py needs.
"""
import zipfile
import xml.etree.ElementTree as ET

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _text(elem):
    return "".join(t.text or "" for t in elem.iter(f"{{{_W}}}t"))


class _Para:
    def __init__(self, elem):
        self.text = _text(elem).strip()


class _Cell:
    def __init__(self, elem):
        self.text = _text(elem).strip()


class _Row:
    def __init__(self, elem):
        self.cells = [_Cell(c) for c in elem.findall(f".//{{{_W}}}tc")]


class _Table:
    def __init__(self, elem):
        self.rows = [_Row(r) for r in elem.findall(f".//{{{_W}}}tr")]


class Document:
    def __init__(self, path):
        with zipfile.ZipFile(str(path)) as z:
            xml = z.read("word/document.xml")
        body = ET.fromstring(xml).find(f".//{{{_W}}}body")
        self.paragraphs = [_Para(p) for p in body.findall(f"{{{_W}}}p")]
        self.tables = [_Table(t) for t in body.findall(f"{{{_W}}}tbl")]
