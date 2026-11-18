"""The command line. At this stage: `interloper --version` and `interloper doctor`.

The commands the method will have are specified in docs/design.md (screen, name, verify, assign, events, report, db);
none of them exists yet, and none is stubbed here: a command that is listed runs.
"""
import argparse
import sys

from . import __version__, doctor


def build_parser():
    parser = argparse.ArgumentParser(
        prog="interloper",
        description="Positive identification of non-human DNA in human sequencing. This version is the groundwork: "
                    "see docs/design.md for the method and docs/roadmap.md for what comes next.")
    parser.add_argument("--version", action="version", version="interloper %s" % __version__)
    sub = parser.add_subparsers(dest="command", metavar="command")
    d = sub.add_parser("doctor", help="check that kraken2, minimap2, samtools and nonhuman-screen are here, with versions",
                       description="Check the tools the method needs. Exit 0 when every one is found, 1 otherwise.")
    d.add_argument("--json", action="store_true", help="the check as JSON")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor.run(as_json=args.json)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
