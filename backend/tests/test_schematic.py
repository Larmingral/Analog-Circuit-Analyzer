from __future__ import annotations

import json
import subprocess
import sys

from SLiCAP.schematic.schematic_data import SchematicData

from isaca_api.schematic import schematic_to_netlist
from isaca_api.slicap_schematic import internal_to_slicap_schematic, slicap_schematic_to_internal
from isaca_api.models import AnalysisPorts, Point, SchematicComponent, SchematicDocument


def test_internal_schematic_exports_expected_rc_netlist(rc_schematic) -> None:
    netlist, diagnostics = schematic_to_netlist(rc_schematic)
    errors = [item for item in diagnostics if item.level == "error"]
    assert errors == []
    assert "V1 in 0 V value={Vin}" in netlist
    assert "R1 in out R value={R}" in netlist
    assert "C1 out 0 C value={C}" in netlist
    assert ".param C=1u R=1k" in netlist
    assert ".source V1" in netlist
    assert ".detector V_out" in netlist


def test_native_slicap_round_trip_preserves_electrical_topology(rc_schematic) -> None:
    native, export_diagnostics = internal_to_slicap_schematic(rc_schematic)
    assert [item for item in export_diagnostics if item.level == "error"] == []
    parsed = SchematicData.from_json(json.dumps(native))
    assert len(parsed.components) == len(rc_schematic.components)
    assert len(parsed.wires) == len(rc_schematic.wires)

    restored, import_diagnostics = slicap_schematic_to_internal(native)
    assert [item for item in import_diagnostics if item.level == "error"] == []
    restored_netlist, restored_diagnostics = schematic_to_netlist(restored)
    assert [item for item in restored_diagnostics if item.level == "error"] == []
    assert "R1 in out R value={R}" in restored_netlist
    assert "C1 out 0 C value={C}" in restored_netlist
    assert restored.analysis.source == "V1"
    assert restored.analysis.detector == "V_out"


def test_unknown_native_objects_are_preserved_read_only(rc_schematic) -> None:
    native, _ = internal_to_slicap_schematic(rc_schematic)
    native["future_field"] = {"value": 7}
    native["components"].append({
        "symbol_name": "FUTURE_DEVICE",
        "instance_id": "Z1",
        "x": 0,
        "y": 0,
    })
    restored, diagnostics = slicap_schematic_to_internal(native)
    exported, _ = internal_to_slicap_schematic(restored)
    assert exported["future_field"] == {"value": 7}
    assert any(component["instance_id"] == "Z1" for component in exported["components"])
    assert any(item.code == "slicap_symbol_read_only" for item in diagnostics)


def test_native_file_is_netlisted_by_official_slicap_cli(tmp_path, rc_schematic) -> None:
    native, diagnostics = internal_to_slicap_schematic(rc_schematic)
    assert [item for item in diagnostics if item.level == "error"] == []
    schematic_path = tmp_path / "rc.slicap_sch"
    netlist_path = tmp_path / "rc.cir"
    schematic_path.write_text(json.dumps(native), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "SLiCAP.schematic.cli",
            "netlist",
            str(schematic_path),
            "-o",
            str(netlist_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr
    netlist = netlist_path.read_text(encoding="utf-8")
    assert "V1 in 0 V value={Vin}" in netlist
    assert "R1 in out R value={R}" in netlist
    assert "C1 out 0 C value={C}" in netlist
    assert ".source V1" in netlist
    assert ".detector V_out" in netlist


def test_subcircuit_block_exports_to_cir_and_reports_native_limit() -> None:
    document = SchematicDocument(
        title="Subcircuit wrapper",
        components=[
            SchematicComponent(
                id="x1",
                refdes="X1",
                device="X",
                position=Point(x=0, y=0),
                model="gain_stage",
                properties={"pins": ["in", "out"]},
            )
        ],
        analysis=AnalysisPorts(source="Vin", detector="V_out"),
    )
    netlist, netlist_diagnostics = schematic_to_netlist(document)
    assert "X1 N001 N002 gain_stage" in netlist
    assert not any(item.code == "unknown_device" for item in netlist_diagnostics)

    _, native_diagnostics = internal_to_slicap_schematic(document)
    assert any(item.code == "slicap_subcircuit_export_unsupported" for item in native_diagnostics)
