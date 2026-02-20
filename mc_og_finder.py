#!/usr/bin/env python3
"""Buscador rápido de nombres OG para Minecraft."""

from __future__ import annotations

import argparse
import itertools
import random
import string
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CURRENT_URL = "https://api.mojang.com/users/profiles/minecraft/{name}"
HISTORY_URL = "https://api.mojang.com/users/profiles/minecraft/{name}?at=0"


@dataclass(slots=True)
class NameResult:
    name: str
    status: str


def load_words(path: Path | None) -> list[str]:
    if path is None:
        return []
    words = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        word = raw.strip().lower()
        if word and not word.startswith("#"):
            words.append(word)
    return words


def builtin_common_words() -> list[str]:
    return [
        "meme", "wolf", "fire", "void", "king", "iron", "gold", "lava", "moon", "star",
        "wind", "snow", "dark", "blue", "pink", "aura", "real", "pro", "hero", "fury",
        "play", "game", "fast", "cool", "zeta", "nova", "byte", "flux", "rojo", "azul",
        "lobo", "luna", "gato", "pato", "rayo", "nube", "foca", "cubo", "rata", "zona",
    ]


def build_charset(kind: str, custom: str | None) -> str:
    if kind == "lower":
        return string.ascii_lowercase
    if kind == "alnum":
        return string.ascii_lowercase + string.digits
    if kind == "digits":
        return string.digits
    if kind == "custom":
        if not custom:
            raise ValueError("--custom-charset es obligatorio cuando --charset=custom")
        unique = "".join(dict.fromkeys(custom.lower()))
        if not unique:
            raise ValueError("--custom-charset no puede estar vacío")
        return unique
    raise ValueError(f"Charset no soportado: {kind}")


def generate_names(
    length: int,
    charset: str,
    prefix: str,
    suffix: str,
    mode: str,
    max_candidates: int,
    words: Iterable[str],
) -> Iterable[str]:
    middle_len = length - len(prefix) - len(suffix)
    if middle_len < 0:
        raise ValueError("prefix + suffix supera --length")

    if mode == "wordlist":
        count = 0
        for w in words:
            if len(w) == length:
                yield w
                count += 1
                if count >= max_candidates:
                    return
        return

    if middle_len == 0:
        yield prefix + suffix
        return

    if mode == "sequential":
        iterator = itertools.product(charset, repeat=middle_len)
        for idx, chunk in enumerate(iterator):
            if idx >= max_candidates:
                return
            yield prefix + "".join(chunk) + suffix
        return

    if mode == "random":
        seen: set[str] = set()
        attempts = 0
        max_attempts = max_candidates * 20
        while len(seen) < max_candidates and attempts < max_attempts:
            attempts += 1
            middle = "".join(random.choice(charset) for _ in range(middle_len))
            candidate = prefix + middle + suffix
            if candidate in seen:
                continue
            seen.add(candidate)
            yield candidate
        return

    raise ValueError(f"Modo no soportado: {mode}")


def fetch_status(url: str, timeout_s: int) -> int:
    req = Request(url, headers={"User-Agent": "mc-og-finder/1.0"})
    try:
        with urlopen(req, timeout=timeout_s) as response:
            return response.getcode()
    except HTTPError as exc:
        return exc.code
    except URLError:
        return 0


def check_name(name: str, timeout_s: int) -> NameResult:
    current = fetch_status(CURRENT_URL.format(name=name), timeout_s)
    if current == 200:
        return NameResult(name=name, status="TAKEN")
    if current == 0:
        return NameResult(name=name, status="UNKNOWN_NETWORK")

    history = fetch_status(HISTORY_URL.format(name=name), timeout_s)
    if history == 200:
        return NameResult(name=name, status="AVAILABLE_PREVIOUSLY_USED")
    if history == 0:
        return NameResult(name=name, status="UNKNOWN_NETWORK")

    return NameResult(name=name, status="AVAILABLE_NEVER_USED")


def run_scan(args: argparse.Namespace) -> list[NameResult]:
    charset = build_charset(args.charset, args.custom_charset)
    words = load_words(Path(args.wordlist) if args.wordlist else None)
    if args.include_builtin_common_words:
        words += builtin_common_words()

    candidates = list(
        dict.fromkeys(
            generate_names(
                length=args.length,
                charset=charset,
                prefix=args.prefix,
                suffix=args.suffix,
                mode=args.mode,
                max_candidates=args.max_candidates,
                words=words,
            )
        )
    )

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(check_name, name, args.timeout_s) for name in candidates]
        return [f.result() for f in futures]


def print_summary(results: list[NameResult]) -> None:
    buckets: dict[str, list[str]] = {
        "AVAILABLE_NEVER_USED": [],
        "AVAILABLE_PREVIOUSLY_USED": [],
        "TAKEN": [],
        "UNKNOWN_NETWORK": [],
    }
    for item in results:
        buckets[item.status].append(item.name)

    print("\n=== RESULTADOS ===")
    for key in ("AVAILABLE_NEVER_USED", "AVAILABLE_PREVIOUSLY_USED", "TAKEN", "UNKNOWN_NETWORK"):
        names = buckets[key]
        print(f"{key}: {len(names)}")
        if names:
            print("  " + ", ".join(names[:20]))


def save_results(path: Path, results: list[NameResult]) -> None:
    lines = ["name,status"]
    lines.extend(f"{r.name},{r.status}" for r in results)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Checker rápido para nombres de Minecraft.")
    parser.add_argument("--length", type=int, default=4)
    parser.add_argument("--charset", choices=["lower", "alnum", "digits", "custom"], default="lower")
    parser.add_argument("--custom-charset", default=None)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--suffix", default="")
    parser.add_argument("--mode", choices=["sequential", "random", "wordlist"], default="random")
    parser.add_argument("--max-candidates", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--timeout-s", type=int, default=10)
    parser.add_argument("--wordlist", default=None)
    parser.add_argument("--include-builtin-common-words", action="store_true")
    parser.add_argument("--out", default="results.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_scan(args)
    print_summary(results)
    save_results(Path(args.out), results)
    print(f"\nCSV guardado en: {args.out}")


if __name__ == "__main__":
    main()
