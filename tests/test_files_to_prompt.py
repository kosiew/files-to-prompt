import os
from sys import stderr

import pytest
from click.testing import CliRunner

from files_to_prompt.cli import cli


def remove_tmpdir_prefix(output, tmpdir):
    return output.replace(str(tmpdir), "")


def test_basic_functionality(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/file1.txt", "w") as f:
            f.write("Contents of file1")
        with open("test_dir/file2.txt", "w") as f:
            f.write("Contents of file2")

        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0
        assert "test_dir/file1.txt" in result.output
        assert "Contents of file1" in result.output
        assert "test_dir/file2.txt" in result.output
        assert "Contents of file2" in result.output


def test_include_hidden(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/.hidden.txt", "w") as f:
            f.write("Contents of hidden file")

        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0
        assert "test_dir/.hidden.txt" not in result.output

        result = runner.invoke(cli, ["test_dir", "--include-hidden"])
        assert result.exit_code == 0
        assert "test_dir/.hidden.txt" in result.output
        assert "Contents of hidden file" in result.output


def test_ignore_gitignore(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/.gitignore", "w") as f:
            f.write("ignored.txt")
        with open("test_dir/ignored.txt", "w") as f:
            f.write("This file should be ignored")
        with open("test_dir/included.txt", "w") as f:
            f.write("This file should be included")

        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0
        assert "test_dir/ignored.txt" not in result.output
        assert "test_dir/included.txt" in result.output

        result = runner.invoke(cli, ["test_dir", "--ignore-gitignore"])
        assert result.exit_code == 0
        assert "test_dir/ignored.txt" in result.output
        assert "This file should be ignored" in result.output
        assert "test_dir/included.txt" in result.output


def test_multiple_paths(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir1")
        with open("test_dir1/file1.txt", "w") as f:
            f.write("Contents of file1")
        os.makedirs("test_dir2")
        with open("test_dir2/file2.txt", "w") as f:
            f.write("Contents of file2")
        with open("single_file.txt", "w") as f:
            f.write("Contents of single file")

        result = runner.invoke(cli, ["test_dir1", "test_dir2", "single_file.txt"])
        assert result.exit_code == 0
        assert "test_dir1/file1.txt" in result.output
        assert "Contents of file1" in result.output
        assert "test_dir2/file2.txt" in result.output
        assert "Contents of file2" in result.output
        assert "single_file.txt" in result.output
        assert "Contents of single file" in result.output


def test_ignore_patterns(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/file_to_ignore.txt", "w") as f:
            f.write("This file should be ignored due to ignore patterns")
        with open("test_dir/file_to_include.txt", "w") as f:
            f.write("This file should be included")

        result = runner.invoke(cli, ["test_dir", "--ignore", "*.txt"])
        assert result.exit_code == 0
        assert "test_dir/file_to_ignore.txt" not in result.output
        assert "This file should be ignored due to ignore patterns" not in result.output
        assert "test_dir/file_to_include.txt" not in result.output

        result = runner.invoke(cli, ["test_dir", "--ignore", "file_to_ignore.*"])
        assert result.exit_code == 0
        assert "test_dir/file_to_ignore.txt" not in result.output
        assert "This file should be ignored due to ignore patterns" not in result.output
        assert "test_dir/file_to_include.txt" in result.output
        assert "This file should be included" in result.output


def test_mixed_paths_with_options(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/.gitignore", "w") as f:
            f.write("ignored_in_gitignore.txt\n.hidden_ignored_in_gitignore.txt")
        with open("test_dir/ignored_in_gitignore.txt", "w") as f:
            f.write("This file should be ignored by .gitignore")
        with open("test_dir/.hidden_ignored_in_gitignore.txt", "w") as f:
            f.write("This hidden file should be ignored by .gitignore")
        with open("test_dir/included.txt", "w") as f:
            f.write("This file should be included")
        with open("test_dir/.hidden_included.txt", "w") as f:
            f.write("This hidden file should be included")
        with open("single_file.txt", "w") as f:
            f.write("Contents of single file")

        result = runner.invoke(cli, ["test_dir", "single_file.txt"])
        assert result.exit_code == 0
        assert "test_dir/ignored_in_gitignore.txt" not in result.output
        assert "test_dir/.hidden_ignored_in_gitignore.txt" not in result.output
        assert "test_dir/included.txt" in result.output
        assert "test_dir/.hidden_included.txt" not in result.output
        assert "single_file.txt" in result.output
        assert "Contents of single file" in result.output

        result = runner.invoke(cli, ["test_dir", "single_file.txt", "--include-hidden"])
        assert result.exit_code == 0
        assert "test_dir/ignored_in_gitignore.txt" not in result.output
        assert "test_dir/.hidden_ignored_in_gitignore.txt" not in result.output
        assert "test_dir/included.txt" in result.output
        assert "test_dir/.hidden_included.txt" in result.output
        assert "single_file.txt" in result.output
        assert "Contents of single file" in result.output

        result = runner.invoke(
            cli, ["test_dir", "single_file.txt", "--ignore-gitignore"]
        )
        assert result.exit_code == 0
        assert "test_dir/ignored_in_gitignore.txt" in result.output
        assert "test_dir/.hidden_ignored_in_gitignore.txt" not in result.output
        assert "test_dir/included.txt" in result.output
        assert "test_dir/.hidden_included.txt" not in result.output
        assert "single_file.txt" in result.output
        assert "Contents of single file" in result.output

        result = runner.invoke(
            cli,
            ["test_dir", "single_file.txt", "--ignore-gitignore", "--include-hidden"],
        )
        assert result.exit_code == 0
        assert "test_dir/ignored_in_gitignore.txt" in result.output
        assert "test_dir/.hidden_ignored_in_gitignore.txt" in result.output
        assert "test_dir/included.txt" in result.output
        assert "test_dir/.hidden_included.txt" in result.output
        assert "single_file.txt" in result.output
        assert "Contents of single file" in result.output


def test_include_binary(tmpdir):
    runner = CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        # Create a binary file
        with open("test_dir/binary_file.bin", "wb") as f:
            f.write(b"\x00\xFF\x00\xFF")
        # Create a text file
        with open("test_dir/text_file.txt", "w") as f:
            f.write("This is a text file")

        # Run without --include-binary; binary files should be skipped
        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0
        stdout = result.stdout
        stderr = result.stderr
        stderr = remove_tmpdir_prefix(stderr, tmpdir)
        assert "test_dir/text_file.txt" in stdout
        assert "This is a text file" in stdout
        assert "test_dir/binary_file.bin" not in stdout
        assert f"Warning: Skipping non-text file /test_dir/binary_file.bin" in stderr

        # Run with --include-binary; binary files should be included
        result = runner.invoke(cli, ["test_dir", "--include-binary"])
        stdout = result.stdout
        stderr = result.stderr
        assert stderr == ""
        assert "test_dir/text_file.txt" in stdout
        assert "This is a text file" in stdout
        assert "test_dir/binary_file.bin" in stdout
        # Contents of binary file may not be printable, so we don't check them
        # Also, there should be no warning about skipping the binary file
        assert "Warning: Skipping non-text file test_dir/binary_file.bin" not in stderr
        assert result.exit_code == 0


def test_print_dir_structure(tmpdir):
    runner = CliRunner()
    with tmpdir.as_cwd():
        # Create directory structure
        os.makedirs("test_dir/subdir")
        with open("test_dir/file1.txt", "w") as f:
            f.write("file1 content")  # 14 characters including the space
        with open("test_dir/subdir/file2.txt", "w") as f:
            f.write("file2 content in subdir")  # 23 characters including spaces

        # Run without --print-dir-structure
        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0
        assert "Directory structure and lengths:" not in result.output

        # Run with --print-dir-structure
        result = runner.invoke(cli, ["test_dir", "--print-dir-structure"])
        output = result.output
        # replace tmpdir with "" to make the test more robust
        output = remove_tmpdir_prefix(output, tmpdir)

        assert "Directory structure and lengths:" in output
        assert "/subdir (length: 23)" in output
        assert "Total length: 36" in output
        assert f"/test_dir (length: 36)" in output
        assert result.exit_code == 0


def test_binary_file_warning(tmpdir):
    runner = CliRunner(mix_stderr=False)
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/binary_file.bin", "wb") as f:
            f.write(b"\xff")
        with open("test_dir/text_file.txt", "w") as f:
            f.write("This is a text file")

        result = runner.invoke(cli, ["test_dir"])
        assert result.exit_code == 0

        stdout = result.stdout
        stderr = result.stderr

        # replace tmpdir with "" to make the test more robust
        stderr = remove_tmpdir_prefix(stderr, tmpdir)

        assert "test_dir/text_file.txt" in stdout
        assert "This is a text file" in stdout
        assert "\ntest_dir/binary_file.bin" not in stdout
        assert f"Warning: Skipping non-text file /test_dir/binary_file.bin" in stderr


@pytest.mark.parametrize(
    "args", (["test_dir"], ["test_dir/file1.txt", "test_dir/file2.txt"])
)
def test_xml_format_dir(tmpdir, args):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/file1.txt", "w") as f:
            f.write("Contents of file1.txt")
        with open("test_dir/file2.txt", "w") as f:
            f.write("Contents of file2.txt")
        result = runner.invoke(cli, args + ["--cxml"])
        assert result.exit_code == 0
        actual = result.output
        actual = remove_tmpdir_prefix(actual, tmpdir)
        expected = f"""
<documents>
<document index="1">
<source>/test_dir/file1.txt</source>
<document_content>
Contents of file1.txt
</document_content>
</document>
<document index="2">
<source>/test_dir/file2.txt</source>
<document_content>
Contents of file2.txt
</document_content>
</document>
</documents>
"""
        assert expected.strip() == actual.strip()


@pytest.mark.parametrize("arg", ("-o", "--output"))
def test_output_option(tmpdir, arg):
    runner = CliRunner()
    with tmpdir.as_cwd():
        os.makedirs("test_dir")
        with open("test_dir/file1.txt", "w") as f:
            f.write("Contents of file1.txt")
        with open("test_dir/file2.txt", "w") as f:
            f.write("Contents of file2.txt")
        output_file = "output.txt"
        result = runner.invoke(
            cli, ["test_dir", arg, output_file], catch_exceptions=False
        )
        assert result.exit_code == 0
        assert not result.output
        with open(output_file, "r") as f:
            actual = f.read()
            actual = remove_tmpdir_prefix(actual, tmpdir)
            expected = f"""
/test_dir/file1.txt
---
Contents of file1.txt

---
/test_dir/file2.txt
---
Contents of file2.txt

---
"""
            assert expected.strip() == actual.strip()
