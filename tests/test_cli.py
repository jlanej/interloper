"""The groundwork's one command: `interloper doctor` reports the tools the method needs, and fails when one is missing."""
import io
import json
import os
import stat

import pytest

import interloper
from interloper import cli, doctor


def fake_program(directory, name, output):
    """A program that prints `output` whatever it is asked."""
    path = os.path.join(str(directory), name)
    with open(path, "w") as fh:
        fh.write("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\n" % output)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def test_version(capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(["--version"])
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == "interloper %s" % interloper.__version__


def test_no_command_prints_help(capsys):
    assert cli.main([]) == 0
    assert "doctor" in capsys.readouterr().out


def test_first_line_skips_blank_lines():
    assert doctor.first_line("\n\n  Kraken version 2.17.1\nCopyright 2013-2023\n") == "Kraken version 2.17.1"
    assert doctor.first_line("") == ""


def test_doctor_fails_when_a_program_is_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))            # an empty directory: nothing is on PATH
    monkeypatch.setattr(doctor, "package_version", lambda name: "0.1.8")
    out = io.StringIO()
    assert doctor.run(as_json=True, out=out) == 1
    report = json.loads(out.getvalue())
    assert report["ok"] is False
    assert report["missing"] == ["kraken2", "minimap2", "samtools"]


def test_doctor_fails_when_the_package_is_missing(tmp_path, monkeypatch):
    for name, text in (("kraken2", "Kraken version 2.17.1"), ("minimap2", "2.30-r1287"), ("samtools", "samtools 1.22.1")):
        fake_program(tmp_path, name, text)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + "/bin" + os.pathsep + "/usr/bin")   # /bin: the fakes' sh and cat
    monkeypatch.setattr(doctor, "package_version", lambda name: None)
    out = io.StringIO()
    assert doctor.run(as_json=True, out=out) == 1
    assert json.loads(out.getvalue())["missing"] == ["nonhuman-screen"]


def test_doctor_reports_each_tool_and_its_version(tmp_path, monkeypatch):
    for name, text in (("kraken2", "Kraken version 2.17.1\nCopyright 2013-2023"), ("minimap2", "2.30-r1287"),
                       ("samtools", "samtools 1.22.1\nUsing htslib 1.22.1")):
        fake_program(tmp_path, name, text)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + "/bin" + os.pathsep + "/usr/bin")
    monkeypatch.setattr(doctor, "package_version", lambda name: "0.1.8")
    out = io.StringIO()
    assert doctor.run(as_json=True, out=out) == 0
    report = json.loads(out.getvalue())
    assert report["ok"] is True and report["missing"] == []
    found = dict((t["name"], t) for t in report["tools"])
    assert found["kraken2"]["version"] == "Kraken version 2.17.1" and found["kraken2"]["where"] == str(tmp_path / "kraken2")
    assert found["minimap2"]["version"] == "2.30-r1287"
    assert found["samtools"]["version"] == "samtools 1.22.1"
    assert found["nonhuman-screen"]["version"] == "0.1.8" and found["nonhuman-screen"]["kind"] == "python package"
    # the plain form says the same and ends "ok"
    text = io.StringIO()
    assert doctor.run(out=text) == 0
    assert text.getvalue().rstrip().endswith("ok") and "Kraken version 2.17.1" in text.getvalue()


def test_doctor_reads_version_text_that_is_not_utf8(tmp_path, monkeypatch):
    path = os.path.join(str(tmp_path), "samtools")
    with open(path, "wb") as fh:                         # a byte no UTF-8 text holds, after the first line
        fh.write(b"#!/bin/sh\nprintf 'samtools 1.21\\nflags \\253 here\\n'\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + "/bin" + os.pathsep + "/usr/bin")
    assert doctor.program_version("samtools", ["--version"]) == (path, "samtools 1.21")


def test_cli_doctor_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(doctor, "package_version", lambda name: "0.1.8")
    assert cli.main(["doctor"]) == 1
    assert "MISSING" in capsys.readouterr().out
