#!/usr/bin/env python3
"""Validate the electrical topology that ERC cannot infer from intent.

KiCad ERC accepts passive networks whose clamp pair or filter input is wired to
the wrong node.  This check exports the native E.9 netlists and asserts the
critical T2/T3 node membership used by the ADC protection and SCT burdens.
"""

from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "hardware" / "perforadas-modulares" / "kicad"


def net_nodes(board: str) -> dict[str, set[tuple[str, str]]]:
    schematic = KICAD / f"medidor-{board.lower()}.kicad_sch"
    with tempfile.TemporaryDirectory() as tmp:
        netlist = Path(tmp) / f"{board}.xml"
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
             "-o", str(netlist), str(schematic)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        root = ET.parse(netlist).getroot()
    return {
        net.attrib["name"]: {(node.attrib["ref"], node.attrib["pin"])
                             for node in net.findall("node")}
        for net in root.findall("./nets/net")
    }


def require_net(nets, name, required):
    actual = nets.get(name, set())
    missing = set(required) - actual
    if missing:
        raise AssertionError(f"{name}: missing {sorted(missing)}; actual={sorted(actual)}")


def require_shared_net(nets, required):
    required = set(required)
    for name, actual in nets.items():
        if required <= actual:
            return name
    raise AssertionError(f"No single net contains {sorted(required)}")


def main():
    t2 = net_nodes("T2")
    require_net(t2, "/CH1_ADC", {("R5", "2"), ("C5", "1"),
                                  ("D2", "2"), ("D3", "1"), ("C_ADC_I", "3")})
    require_net(t2, "/CH2_ADC", {("R6", "2"), ("C6", "1"),
                                  ("D4", "2"), ("D5", "1"), ("C_ADC_I", "4")})
    require_net(t2, "/VBIAS", {("J2", "2"), ("J3", "2"),
                                ("R1", "2"), ("R2", "2"),
                                ("C5", "2"), ("C6", "2")})
    require_shared_net(t2, {("J2", "1"), ("R1", "1"), ("R5", "1")})
    require_shared_net(t2, {("J3", "1"), ("R2", "1"), ("R6", "1")})

    t3 = net_nodes("T3")
    require_net(t3, "/V_ADC", {("R7", "2"), ("R8", "1"), ("C9", "1"),
                                ("D6", "2"), ("D7", "1"), ("C_ADC_V", "3")})

    print("E9_SCHEMATIC_TOPOLOGY_OK")


if __name__ == "__main__":
    main()
