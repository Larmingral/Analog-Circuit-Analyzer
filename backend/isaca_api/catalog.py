"""Pinned SLiCAP 5.2.1 device metadata used by the web editor."""

from __future__ import annotations

from copy import deepcopy


DEVICE_CATALOG: dict[str, dict] = {
    "R": {"label": "Resistor", "prefix": "R", "model": "R", "symbol": "R", "pins": ["pos", "neg"], "defaults": {"value": "?"}, "slicap_defaults": {"value": "0", "dcvar": "0", "noisetemp": "0", "noiseflow": "0", "dcvarlot": "0"}},
    "C": {"label": "Capacitor", "prefix": "C", "model": "C", "symbol": "C", "pins": ["pos", "neg"], "defaults": {"value": "?", "vinit": ""}, "slicap_defaults": {"value": "0", "vinit": "0"}},
    "L": {"label": "Inductor", "prefix": "L", "model": "L", "symbol": "L", "pins": ["pos", "neg"], "defaults": {"value": "?", "iinit": ""}, "slicap_defaults": {"value": "0", "iinit": "0"}},
    "V": {"label": "Voltage source", "prefix": "V", "model": "V", "symbol": "V", "pins": ["outp", "outn"], "defaults": {"value": "?", "dc": ""}, "slicap_defaults": {"value": "0", "dc": "0", "dcvar": "0", "noise": "0"}},
    "I": {"label": "Current source", "prefix": "I", "model": "I", "symbol": "I", "pins": ["outp", "outn"], "defaults": {"value": "?", "dc": ""}, "slicap_defaults": {"value": "0", "dc": "0", "dcvar": "0", "noise": "0"}},
    "G": {"label": "VCCS", "prefix": "G", "model": "G", "symbol": "VCCS", "pins": ["outp", "outn", "inp", "inn"], "defaults": {"value": "?"}, "slicap_defaults": {"value": "0"}},
    "E": {"label": "VCVS", "prefix": "E", "model": "E", "symbol": "VCVS", "pins": ["outp", "outn", "inp", "inn"], "defaults": {"value": "?"}, "slicap_defaults": {"value": "0"}},
    "F": {"label": "CCCS", "prefix": "F", "model": "F", "symbol": "CCCS", "pins": ["outp", "outn"], "refs": 1, "defaults": {"value": "?"}, "slicap_defaults": {"value": "0"}},
    "H": {"label": "CCVS", "prefix": "H", "model": "H", "symbol": "CCVS", "pins": ["outp", "outn"], "refs": 1, "defaults": {"value": "?"}, "slicap_defaults": {"value": "0"}},
    "M": {
        "label": "MOS small signal",
        "prefix": "M",
        "model": "M",
        "symbol": "M",
        "pins": ["D", "G", "S", "B"],
        "defaults": {"cgs": "", "cgb": "", "cdg": "", "cdb": "", "csb": "", "gm": "", "gb": "", "go": ""},
        "slicap_defaults": {"cgs": "0", "cgb": "0", "cdg": "0", "cdb": "0", "csb": "0", "gm": "1m", "gb": "0", "go": "0"},
    },
    "QV": {
        "label": "BJT small signal",
        "prefix": "Q",
        "model": "QV",
        "symbol": "QV",
        "pins": ["C", "B", "E", "S"],
        "defaults": {"gm": "", "go": "", "gbc": "", "gpi": "", "rb": "", "cpi": "", "cbc": "", "cbx": ""},
        "slicap_defaults": {"gm": "40m", "go": "0", "gbc": "0", "gpi": "2.5k", "rb": "0", "cpi": "0", "cbc": "0", "cbx": "0", "cs": "0"},
    },
    "X": {"label": "Subcircuit", "prefix": "X", "model": None, "pins": [], "defaults": {}},
    "GROUND": {"label": "Ground", "prefix": None, "model": None, "symbol": "0", "pins": ["0"], "defaults": {"name": "0"}},
    "PORT": {"label": "Named port", "prefix": None, "model": None, "symbol": "port", "pins": ["port"], "defaults": {"name": ""}},
}


def device_catalog() -> dict[str, dict]:
    """Return a defensive copy of the pinned editor catalog."""

    return deepcopy(DEVICE_CATALOG)
