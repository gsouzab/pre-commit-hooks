from pre_commit_hooks.max_lines import files_exceeding_max_lines
from pre_commit_hooks.max_lines import main
from pre_commit_hooks.util import cmd_output
from testing.util import git_commit


def test_nothing_added(temp_git_dir):
    with temp_git_dir.as_cwd():
        assert files_exceeding_max_lines(["f.py"], 0) == 0


def test_file_exceeding_max_lines(temp_git_dir):
    with temp_git_dir.as_cwd():
        temp_git_dir.join("f.py").write("a\n" * 10)

        assert files_exceeding_max_lines(["f.py"], 10) == 0

        assert files_exceeding_max_lines(["f.py"], 9) == 1


def test_file_exceeding_max_lines_with_modified(temp_git_dir):
    with temp_git_dir.as_cwd():
        with open("f.py", "w") as f:
            f.write("a\n" * 10)
        cmd_output("git", "add", "f.py")
        git_commit("-m", "commit")

        assert files_exceeding_max_lines(["f.py"], 5, ignore_modified=True) == 1

        remove_lines("f.py", 1)

        cmd_output("git", "add", "f.py")

        assert files_exceeding_max_lines(["f.py"], 5, ignore_modified=True) == 0


def test_file_exceeding_max_lines_with_large_file(temp_git_dir):
    with temp_git_dir.as_cwd():
        temp_git_dir.join("f.py").write("a\n" * 100000)
        assert files_exceeding_max_lines(["f.py"], 100000) == 0
        assert files_exceeding_max_lines(["f.py"], 99999) == 1


def test_files_exceeding_max_lines_with_extension(temp_git_dir):
    with temp_git_dir.as_cwd():
        temp_git_dir.join("f.py").write("a\n" * 10)
        temp_git_dir.join("f.txt").write("a\n" * 10)
        assert files_exceeding_max_lines(["f.py", "f.txt"], 9, extension="py") == 1
        assert files_exceeding_max_lines(["f.py", "f.txt"], 9, extension="json") == 0


def test_integration(temp_git_dir):
    with temp_git_dir.as_cwd():
        assert main(argv=[]) == 0

        temp_git_dir.join("f.py").write("a\n" * 10)
        cmd_output("git", "add", "f.py")
        git_commit("-m", "commit")
        # should not fail with default
        assert main(argv=["f.py"]) == 0

        # should fail with max size of 9
        assert main(argv=["f.py", "--max-lines", "9"]) == 1

        # should fail with max size of 9 and extension
        assert main(argv=["f.py", "--max-lines", "9", "--extension", "py"]) == 1

        # should not fail with max size of 9 and extension
        assert main(argv=["f.py", "--max-lines", "9", "--extension", "txt"]) == 0

        # should fail with ignore modified
        assert main(argv=["f.py", "--max-lines", "9", "--ignore-modified"]) == 1

        remove_lines("f.py", 1)
        cmd_output("git", "add", "f.py")
        # should not fail with ignore modified
        assert main(argv=["f.py", "--max-lines", "1", "--ignore-modified"]) == 0


def remove_lines(filename: str, num_lines: int):
    with open(filename, "r+") as f:
        lines = f.readlines()

        f.seek(0)
        f.truncate()

        f.writelines(lines[num_lines:])
