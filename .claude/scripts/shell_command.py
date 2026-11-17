"""Shell-command parsing shared by the hooks that inspect a Bash tool command.

Splits a command into its simple commands with the directory each one runs in, and resolves the
directory and subcommand of a `git` invocation. Standard library only.
"""

import os
import re
import shlex


def _tokens_of(part):
    try:
        return shlex.split(part)
    except ValueError:
        return part.split()


def segments_with_directory(command, cwd):
    """Split a shell command into its simple commands, each with the directory it runs in.

    Splits on &&, ||, ;, | and newlines; tokenizes each part with shlex (falling back to
    str.split on a shlex error); drops leading VAR=value assignments. A `cd <dir>` part changes
    the directory for the parts after it (relative to the current one, ~ expanded) and is not
    itself returned. Empty parts are dropped.
    """
    directory = cwd
    result = []
    for part in re.split(r"&&|\|\||;|\||\n", command):
        part = part.strip()
        if not part:
            continue
        tokens = _tokens_of(part)
        if len(tokens) >= 2 and tokens[0] == "cd":
            directory = os.path.join(directory, os.path.expanduser(tokens[1]))
            continue
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if tokens:
            result.append((tokens, directory))
    return result


def git_target(tokens, directory):
    """For a `git ...` command: the directory it acts on and the arguments from the subcommand on.

    Applies every `-C <dir>` (relative to `directory`), skips `-c <key=value>` and other leading
    options. Returns None when tokens[0] is not `git`. Example:
    git_target(["git", "-C", "R", "commit", "-m", "x"], "/a") == ("/a/R", ["commit", "-m", "x"])
    """
    if not tokens or tokens[0] != "git":
        return None
    rest, i = tokens[1:], 0
    while i < len(rest) and rest[i].startswith("-"):
        if rest[i] == "-C" and i + 1 < len(rest):
            directory = os.path.join(directory, rest[i + 1])
            i += 1
        elif rest[i] == "-c":
            i += 1
        i += 1
    return directory, rest[i:]
