"""Thread-safe, version-pinned boundary around SLiCAP 5.2.1 public APIs."""

from __future__ import annotations

import json
import locale
import os
import threading
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable

import sympy as sp

from .models import AnalysisRequest, CircuitDocument
from .netlist import normalize_netlist
from .parameters import numeric_substitutions


SUPPORTED_SLICAP_VERSION = "5.2.1"
_SLICAP_LOCK = threading.RLock()


class SLiCAPAdapterError(RuntimeError):
    """Base error raised at the SLiCAP integration boundary."""


class SLiCAPVersionError(SLiCAPAdapterError):
    """Raised when the active SLiCAP package is not the pinned release."""


class MissingNumericParameters(SLiCAPAdapterError):
    """Raised before numeric analysis when required parameters are unresolved."""

    def __init__(self, names: Iterable[str]):
        self.names = tuple(sorted(set(names)))
        super().__init__("Numeric analysis requires values for: " + ", ".join(self.names))


def installed_slicap_version() -> str:
    """Return the installed SLiCAP distribution version without importing it."""

    try:
        return version("SLiCAP")
    except PackageNotFoundError as error:
        raise SLiCAPVersionError("SLiCAP is not installed in the active environment.") from error


def assert_slicap_version() -> str:
    """Require the exact SLiCAP release used by this adapter."""

    installed = installed_slicap_version()
    if installed != SUPPORTED_SLICAP_VERSION:
        raise SLiCAPVersionError(
            f"This application requires SLiCAP=={SUPPORTED_SLICAP_VERSION}; found {installed}."
        )
    return installed


@contextmanager
def _project_directory(path: Path):
    """Serialize SLiCAP global state and execute from one isolated project."""

    with _SLICAP_LOCK:
        previous = Path.cwd()
        path.mkdir(parents=True, exist_ok=True)
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, sp.MatrixBase):
        return [[_json_value(item) for item in row] for row in value.tolist()]
    if isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_value(value.tolist())
    return str(value)


def _result_fields(result: Any, fields: Iterable[str]) -> dict[str, Any]:
    return {field: _json_value(getattr(result, field)) for field in fields if hasattr(result, field)}


def _write_slicap_working_netlist(path: Path, text: str) -> tuple[str, int, bool]:
    """Write the parser copy using the platform encoding used by SLiCAP's open()."""

    lines = text.splitlines()
    title_sanitized = bool(lines and any(ord(char) > 127 for char in lines[0]))
    if title_sanitized:
        lines[0] = '"ISACA imported circuit"'
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    encoding = locale.getpreferredencoding(False) or "utf-8"
    encoded = text.encode(encoding, errors="replace")
    recovered = encoded.decode(encoding)
    replacements = sum(left != right for left, right in zip(text, recovered))
    replacements += abs(len(text) - len(recovered))
    path.write_bytes(encoded)
    return encoding, replacements, title_sanitized


def _circuit_summary(circuit: Any) -> dict[str, Any]:
    elements = {}
    for refdes, element in sorted(getattr(circuit, "elements", {}).items()):
        elements[str(refdes)] = {
            "model": str(getattr(element, "model", "")),
            "nodes": list(getattr(element, "nodes", [])),
            "params": _json_value(getattr(element, "params", {})),
        }
    return {
        "title": str(getattr(circuit, "title", "")),
        "source": _json_value(getattr(circuit, "source", None)),
        "detector": _json_value(getattr(circuit, "detector", None)),
        "nodes": sorted(str(node) for node in getattr(circuit, "nodes", [])),
        "parameter_definitions": _json_value(getattr(circuit, "parDefs", {})),
        "elements": elements,
    }


def _make_circuit(sl: Any) -> Any:
    """Call SLiCAP and translate its opaque unknown-model exception."""

    try:
        return sl.makeCircuit("input.cir", imgWidth=None, expansion=False)
    except KeyError as error:
        # SLiCAP 5.2.1 raises KeyError(False) after reporting an unknown
        # device model. Translate that implementation detail at our boundary.
        if error.args == (False,):
            raise SLiCAPAdapterError(
                "SLiCAP rejected an undefined or invalid element model; "
                "check device model names and required .model definitions."
            ) from error
        raise


class SLiCAP521Adapter:
    """Run numeric and symbolic analyses in isolated per-job directories."""

    def __init__(self, run_root: str | Path):
        self.run_root = Path(run_root).resolve()
        self.version = assert_slicap_version()

    def prepare_document(self, request: AnalysisRequest) -> CircuitDocument:
        """Normalize input and resolve parameter provenance before execution."""

        from .models import NormalizeRequest

        return normalize_netlist(
            NormalizeRequest(
                netlist_text=request.netlist_text,
                parameter_overrides=request.parameter_overrides,
                use_slicap_defaults=request.use_slicap_defaults,
            )
        )

    def analyze(self, job_id: str, request: AnalysisRequest) -> dict[str, Any]:
        """Execute requested SLiCAP and SFG analyses and return structured data."""

        document = self.prepare_document(request)
        substitutions, missing = numeric_substitutions(document.parameters)
        numeric_modes = {"laplace", "pz", "matrix", "noise"}
        if request.numeric and numeric_modes.intersection(request.modes) and missing:
            raise MissingNumericParameters(missing)

        project_dir = self.run_root / job_id
        cir_dir = project_dir / "cir"
        artifacts_dir = project_dir / "artifacts"
        cir_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        netlist_path = cir_dir / "input.cir"
        working_encoding, replacements, title_sanitized = _write_slicap_working_netlist(
            netlist_path, document.netlist_text
        )

        result: dict[str, Any] = {
            "software": {
                "slicap": self.version,
                "working_netlist_encoding": working_encoding,
                "transcoding_replacements": replacements,
                "title_sanitized": title_sanitized,
            },
            "circuit": document.model_dump(mode="json"),
            "analyses": {},
            "artifacts": {},
        }
        with _project_directory(project_dir):
            import SLiCAP as sl

            sl.initProject(f"ISACA analysis {job_id}", report_dirs=True)
            circuit = _make_circuit(sl)
            if circuit is None:
                raise SLiCAPAdapterError("SLiCAP did not return a circuit object.")
            circuit_errors = int(getattr(circuit, "errors", 0) or 0)
            if circuit_errors:
                raise SLiCAPAdapterError(f"SLiCAP reported {circuit_errors} circuit error(s).")
            result["flattened_circuit"] = _circuit_summary(circuit)
            pardefs = {sp.Symbol(name): sp.Float(value) for name, value in substitutions.items()}
            numeric = bool(request.numeric)

            if "laplace" in request.modes:
                laplace = sl.doLaplace(circuit, pardefs=pardefs or None, numeric=numeric)
                result["analyses"]["laplace"] = _result_fields(
                    laplace,
                    ("laplace", "numer", "denom", "DCvalue", "M", "Iv", "Dv"),
                )
            if "pz" in request.modes:
                pz = sl.doPZ(circuit, pardefs=pardefs or None, numeric=numeric)
                result["analyses"]["pz"] = _result_fields(
                    pz,
                    ("poles", "zeros", "DCvalue", "laplace", "numer", "denom"),
                )
            if "matrix" in request.modes:
                matrix = sl.doMatrix(circuit, pardefs=pardefs or None, numeric=numeric)
                result["analyses"]["matrix"] = _result_fields(matrix, ("M", "Iv", "Dv"))
            if "noise" in request.modes:
                noise = sl.doNoise(circuit, pardefs=pardefs or None, numeric=numeric)
                result["analyses"]["noise"] = _result_fields(
                    noise,
                    ("onoise", "inoise", "onoiseTerms", "inoiseTerms"),
                )

            if "symbolic" in request.modes:
                result["analyses"]["symbolic"] = self._run_symbolic(
                    netlist_path,
                    artifacts_dir,
                    request,
                    substitutions,
                )

        input_copy = artifacts_dir / "normalized.cir"
        input_copy.write_text(document.netlist_text, encoding="utf-8")
        result["artifacts"]["normalized.cir"] = str(input_copy)
        manifest = artifacts_dir / "result.json"
        manifest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        result["artifacts"]["result.json"] = str(manifest)
        return result

    def _run_symbolic(
        self,
        netlist_path: Path,
        artifacts_dir: Path,
        request: AnalysisRequest,
        substitutions: dict[str, float],
    ) -> dict[str, Any]:
        """Run the versioned standalone SFG package and persist its reports."""

        try:
            from sfg_prototype import (
                SimplificationConfig,
                error_trace_report,
                operation_ranking_report,
                root_localization_summary_report,
                simplification_report,
                simplify_netlist,
                subrange_simplification_report,
            )
        except ImportError as error:
            raise SLiCAPAdapterError(
                "The sfg-prototype wheel is not installed in slicap5_env."
            ) from error

        config = SimplificationConfig(
            frequency_range_hz=request.frequency_range_hz,
            magnitude_error_db=request.magnitude_error_db,
            phase_error_deg=request.phase_error_deg,
        )
        simplified = simplify_netlist(
            str(netlist_path),
            config=config,
            substitutions=substitutions,
        )
        reports = {
            "simplification.md": simplification_report(simplified),
            "subrange_simplification.md": subrange_simplification_report(simplified),
            "operation_ranking.md": operation_ranking_report(simplified),
            "error_trace.md": error_trace_report(simplified),
            "root_localization.md": root_localization_summary_report(simplified),
        }
        paths: dict[str, str] = {}
        for name, content in reports.items():
            path = artifacts_dir / name
            path.write_text(content, encoding="utf-8")
            paths[name] = str(path)
        return {
            "accepted_steps": len(simplified.accepted_steps),
            "rejected_steps": len(simplified.rejected_steps),
            "subranges": len(simplified.subrange_results),
            "reports": paths,
        }
