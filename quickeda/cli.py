"""命令行入口：`quickeda data.csv -o report.html`。"""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__, profile


def _force_utf8_stdout() -> None:
    """Windows 控制台默认 GBK，遇到中文 / ✓ 会崩；尽量切到 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(
        prog="quickeda",
        description="一行命令，秒出数据探索分析（EDA）报告。",
    )
    parser.add_argument("data", help="数据文件路径（csv/tsv/xlsx/parquet/json）")
    parser.add_argument("-o", "--output", help="报告输出路径（默认 <文件名>_report.html）")
    parser.add_argument("-t", "--title", default="数据探查报告", help="报告标题")
    parser.add_argument("--sep", help="分隔符（如 ';'），透传给 pandas")
    parser.add_argument("--encoding", help="文件编码（如 gbk）")
    parser.add_argument("--open", action="store_true", help="生成后自动用浏览器打开")
    parser.add_argument("-v", "--version", action="version",
                        version=f"QuickEDA {__version__}")
    args = parser.parse_args(argv)

    read_kwargs = {}
    if args.sep:
        read_kwargs["sep"] = args.sep
    if args.encoding:
        read_kwargs["encoding"] = args.encoding

    start = time.perf_counter()
    try:
        out = profile(
            args.data,
            args.output,
            title=args.title,
            open_browser=args.open,
            **read_kwargs,
        )
    except FileNotFoundError:
        print(f"✗ 找不到文件：{args.data}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - CLI 顶层，友好提示即可
        print(f"✗ 生成报告失败：{exc}", file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - start
    print(f"✓ 报告已生成：{out}  （耗时 {elapsed:.2f}s）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
