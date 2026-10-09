#!/usr/bin/env python3
from qscope.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["validate-submission", *__import__("sys").argv[1:]]))
