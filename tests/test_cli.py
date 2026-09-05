"""Tests for the Temporal Reasoning CLI."""

from io import StringIO
import tempfile
from pathlib import Path
from temporal_reasoning.cli import main, build_parser


def test_cli_help():
    parser = build_parser()
    assert parser.prog == "temporal-reasoning"


def test_cli_query_with_statements(capsys):
    ret = main([
        "-s", "Alice arrived before Bob.",
        "-s", "Bob left before Charlie.",
        "-q", "Alice", "Charlie",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Relation (Alice -> Charlie): BEFORE" in captured.out
    assert "Provenance: Transitivity" in captured.out


def test_cli_consistency_check(capsys):
    ret = main([
        "-s", "Event X before Event Y.",
        "-s", "Event Y before Event X.",
        "-c",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Found 1 temporal conflict" in captured.out or "conflict" in captured.out.lower()


def test_cli_evaluate(capsys):
    ret = main(["--evaluate", "data/examples.json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Temporal Reasoning Evaluation" in captured.out
    assert "Overall Accuracy" in captured.out


def test_cli_file_input_and_dot_export(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        in_file = Path(tmpdir) / "test_in.txt"
        out_dot = Path(tmpdir) / "test_out.dot"

        in_file.write_text("Alpha before Beta.\nBeta before Gamma.", encoding="utf-8")

        ret = main([
            "-i", str(in_file),
            "-q", "Alpha", "Gamma",
            "--export-dot", str(out_dot),
        ])
        assert ret == 0
        captured = capsys.readouterr()
        assert "BEFORE" in captured.out
        assert out_dot.exists()
        assert "digraph TemporalGraph" in out_dot.read_text(encoding="utf-8")
