from __future__ import annotations

import argparse
import os
import subprocess
from typing import Sequence
from pre_commit_hooks.util import cmd_output


def modified_files_decreased_lines(max_lines: int) -> set[str]:
    """Return a set of modified files that have less lines than before."""
    diff = cmd_output("git", "diff", "--numstat", "--staged", "--diff-filter=M")

    print(f"{diff.splitlines()}")
    filenames = set()
    for line in diff.splitlines():
        added, deleted, filename = line.split("\t")
        lines_diff = int(added) - int(deleted)
        if lines_diff < 0:
            filenames.add(filename)

    return filenames


def files_exceeding_max_lines(
    filenames: Sequence[str],
    max_lines: int,
    extension: str | None = None,
    *,
    ignore_modified: bool = False,
) -> int:
    """
    Find files that exceed the maximum number of lines.
    return 0 if no files exceed the maximum number of lines, 1 otherwise.
    """
    retv = 0
    filtered_filenames = set(filenames)
    if extension:
        filtered_filenames = {
            filename for filename in filenames if filename.endswith(f".{extension}")
        }

    if ignore_modified:
        print("Ignoring modified files that have less lines than before:")
        modified_files = modified_files_decreased_lines(max_lines)
        print(modified_files)
        filtered_filenames -= modified_files

    for filename in filtered_filenames:
        if num_lines(filename) > max_lines:
            print(f"{filename} exceeds {max_lines} lines")
            retv = 1

    return retv


def num_lines(filename) -> int:
    if not os.path.isfile(filename):
        return 0

    output = cmd_output("wc", "-l", filename)
    num_lines = int(output.split()[0])
    return num_lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        usage="[filenames] [-e <comma separated folder exceptions>] [-m <max lines>] [-x <extension>] [-p entrypoint]"
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )
    parser.add_argument(
        "-m",
        "--max-lines",
        type=int,
        default=1000,
        help="Maximum number of lines a file can have. Default: 1000",
    )
    parser.add_argument(
        "-e",
        "--exceptions",
        type=str,
        help="Comma separated list of paths to partially match and filter out. Default: none",
    )
    parser.add_argument(
        "-x",
        "--extension",
        type=str,
        help="File extension to analyze. Default: none",
    )
    parser.add_argument(
        "--ignore-modified",
        action="store_true",
        help="Ignore modified files that have less lines than before.",
    )

    args = parser.parse_args(argv)

    return files_exceeding_max_lines(
        args.filenames,
        args.max_lines,
        args.extension,
        ignore_modified=args.ignore_modified,
    )


if __name__ == "__main__":
    raise SystemExit(main())
