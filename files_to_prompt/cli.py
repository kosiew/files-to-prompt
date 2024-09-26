import os
from fnmatch import fnmatch

import click

global_index = 1
total_length = 0
dir_lengths = {}  # Dictionary to keep track of directory lengths


def should_ignore(path, gitignore_rules):
    for rule in gitignore_rules:
        if fnmatch(os.path.basename(path), rule):
            return True
        if os.path.isdir(path) and fnmatch(os.path.basename(path) + "/", rule):
            return True
    return False


def read_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


def is_text_file(file_path):
    # Try to read the first 1024 bytes and decode them
    try:
        with open(file_path, "rb") as file:
            chunk = file.read(1024)
            if b"\0" in chunk:
                return False  # Likely a binary file
            # Attempt to decode the chunk using utf-8
            try:
                chunk.decode("utf-8")
                return True
            except UnicodeDecodeError:
                return False
    except Exception:
        return False


def print_path(writer, path, content, xml):
    if xml:
        print_as_xml(writer, path, content)
    else:
        print_default(writer, path, content)


def print_default(writer, path, content):
    global total_length
    writer(path)
    writer("---")
    writer(content)
    writer("")
    writer("---")
    total_length += len(content)


def print_as_xml(writer, path, content):
    global global_index, total_length
    writer(f'<document index="{global_index}">')
    writer(f"<source>{path}</source>")
    writer("<document_content>")
    writer(content)
    writer("</document_content>")
    writer("</document>")
    total_length += len(content)
    global_index += 1


def update_dir_length(file_path, length, root_path):
    dir_path = os.path.dirname(file_path)
    while True:
        dir_lengths[dir_path] = dir_lengths.get(dir_path, 0) + length
        if dir_path == root_path:
            break
        parent_dir = os.path.dirname(dir_path)
        if parent_dir == dir_path or not parent_dir:
            break
        dir_path = parent_dir


def process_path(
    path,
    include_hidden,
    ignore_gitignore,
    gitignore_rules,
    ignore_patterns,
    writer,
    claude_xml,
    root_path,
    include_binary,
):
    # Default patterns to ignore image and PDF files
    default_ignore_patterns = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.svg",
        "*.tif",
        "*.tiff",
        "*.pdf",
        "*.ico",
        "*.icns",
        "*.webp",
        "*.mp3",
        "*.wav",
        "*.ogg",
        "*.mp4",
        "*.avi",
        "*.mov",
    ]

    # Apply default ignore patterns unless include_binary is True
    if not include_binary:
        ignore_patterns = list(ignore_patterns) + default_ignore_patterns

    if os.path.isfile(path):
        if is_text_file(path):
            # Check if the file matches any ignore patterns
            if any(
                fnmatch(os.path.basename(path), pattern) for pattern in ignore_patterns
            ):
                return
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                # Only print the path and content after successful read
                print_path(writer, path, content, claude_xml)
                update_dir_length(path, len(content), root_path)
            except Exception as e:
                warning_message = f"Warning: Skipping file {path} due to an error: {e}"
                click.echo(click.style(warning_message, fg="red"), err=True)
        else:
            # Check if we should include binary files
            if include_binary:
                # Check if the file matches any ignore patterns
                if any(
                    fnmatch(os.path.basename(path), pattern)
                    for pattern in ignore_patterns
                ):
                    return
                # Attempt to read binary file content as text
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    print_path(writer, path, content, claude_xml)
                    update_dir_length(path, len(content), root_path)
                except Exception as e:
                    warning_message = (
                        f"Warning: Skipping binary file {path} due to an error: {e}"
                    )
                    click.echo(click.style(warning_message, fg="red"), err=True)
            else:
                warning_message = f"Warning: Skipping non-text file {path}"
                click.echo(click.style(warning_message, fg="yellow"), err=True)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            if not ignore_gitignore:
                gitignore_rules.extend(read_gitignore(root))
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(os.path.join(root, d), gitignore_rules)
                ]
                files = [
                    f
                    for f in files
                    if not should_ignore(os.path.join(root, f), gitignore_rules)
                ]

            if ignore_patterns:
                files = [
                    f
                    for f in files
                    if not any(fnmatch(f, pattern) for pattern in ignore_patterns)
                ]

            for file in sorted(files):
                file_path = os.path.join(root, file)
                if is_text_file(file_path):
                    # Check if the file matches any ignore patterns
                    if any(
                        fnmatch(os.path.basename(file_path), pattern)
                        for pattern in ignore_patterns
                    ):
                        continue
                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                        # Only print the path and content after successful read
                        print_path(writer, file_path, content, claude_xml)
                        update_dir_length(file_path, len(content), root_path)
                    except Exception as e:
                        warning_message = (
                            f"Warning: Skipping file {file_path} due to error: {e}"
                        )
                        click.echo(click.style(warning_message, fg="red"), err=True)
                else:
                    # Check if we should include binary files
                    if include_binary:
                        # Check if the file matches any ignore patterns
                        if any(
                            fnmatch(os.path.basename(file_path), pattern)
                            for pattern in ignore_patterns
                        ):
                            continue
                        try:
                            with open(
                                file_path, "r", encoding="utf-8", errors="replace"
                            ) as f:
                                content = f.read()
                            print_path(writer, file_path, content, claude_xml)
                            update_dir_length(file_path, len(content), root_path)
                        except Exception as e:
                            warning_message = f"Warning: Skipping binary file {file_path} due to error: {e}"
                            click.echo(click.style(warning_message, fg="red"), err=True)
                    else:
                        warning_message = f"Warning: Skipping non-text file {file_path}"
                        click.echo(click.style(warning_message, fg="yellow"), err=True)


def print_directory_structure(dir_lengths, writer, root_paths):
    def build_tree():
        tree = {}
        for dir_path in dir_lengths.keys():
            for root_path in root_paths:
                if dir_path.startswith(root_path):
                    rel_path = os.path.relpath(dir_path, root_path)
                    parts = rel_path.split(os.sep)
                    subtree = tree.setdefault(root_path, {})
                    for part in parts:
                        subtree = subtree.setdefault(part, {})
                    break  # Stop after finding the first matching root_path
        return tree

    def print_tree(subtree, path="", level=0):
        for dir_name in sorted(subtree.keys()):
            full_path = os.path.join(path, dir_name) if path else dir_name
            abs_path = os.path.abspath(full_path)
            length = dir_lengths.get(abs_path, 0)
            indent = " " * (level * 4)
            writer(f"{indent}{dir_name}/ (length: {length:,})")

            print_tree(subtree[dir_name], full_path, level + 1)

    tree = build_tree()
    print_tree(tree)


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--include-hidden",
    is_flag=True,
    help="Include files and folders starting with .",
)
@click.option(
    "--ignore-gitignore",
    is_flag=True,
    help="Ignore .gitignore files and include all files",
)
@click.option(
    "ignore_patterns",
    "--ignore",
    multiple=True,
    default=[],
    help="List of patterns to ignore",
)
@click.option(
    "output_file",
    "-o",
    "--output",
    type=click.Path(writable=True),
    help="Output to a file instead of stdout",
)
@click.option(
    "claude_xml",
    "-c",
    "--cxml",
    is_flag=True,
    help="Output in XML-ish format suitable for Claude's long context window.",
)
@click.option(
    "--print-dir-structure",
    is_flag=True,
    help="Print the directory structure and the length in each directory",
)
@click.option(
    "--include-binary",
    is_flag=True,
    help="Include binary files and files with ignored extensions",
)
@click.version_option()
def clii(
    paths,
    include_hidden,
    ignore_gitignore,
    ignore_patterns,
    output_file,
    claude_xml,
    print_dir_structure,
    include_binary,
):
    # Reset global variables
    global global_index, total_length, dir_lengths
    global_index = 1
    total_length = 0
    dir_lengths = {}

    gitignore_rules = []
    writer = click.echo
    fp = None
    if output_file:
        fp = open(output_file, "w", encoding="utf-8")
        writer = lambda s: print(s, file=fp)
    else:
        writer = lambda s: click.echo(s, file=None)

    # Convert paths to absolute paths and store them
    root_paths = [os.path.abspath(path) for path in paths]

    for path in root_paths:
        if not os.path.exists(path):
            raise click.BadArgumentUsage(f"Path does not exist: {path}")
        if not ignore_gitignore:
            gitignore_rules.extend(read_gitignore(os.path.dirname(path)))
        if claude_xml and path == root_paths[0]:
            writer("<documents>")
        process_path(
            path,
            include_hidden,
            ignore_gitignore,
            gitignore_rules,
            ignore_patterns,
            writer,
            claude_xml,
            root_path=path,
            include_binary=include_binary,  # Pass the new parameter
        )
    if claude_xml:
        writer("</documents>")
    if print_dir_structure:
        writer("Directory structure and lengths:")
        print_directory_structure(dir_lengths, writer, root_paths)
        writer(f"Total length: {total_length:,}")
    if fp:
        fp.close()


if __name__ == "__main__":
    cli()
