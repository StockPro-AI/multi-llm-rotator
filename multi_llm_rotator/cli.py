"""CLI for multi-llm-rotator.

Usage:
    mlr add gemini g1 --key AIza... --model gemini-2.0-flash
    mlr add claude c1 --key sk-ant-... --model claude-opus-4-5
    mlr add openai o1 --key sk-... --model gpt-4o
    mlr list
    mlr list gemini
    mlr remove gemini g1
    mlr enable gemini g1
    mlr disable gemini g1
    mlr clear-rate-limits
    mlr chat gemini "What is the capital of Germany?"
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .accounts import AccountManager
from .rotator import LLMRotator, RotationStrategy

# Import providers to trigger auto-registration
from .providers import GeminiProvider, ClaudeProvider, OpenAIProvider  # noqa: F401


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mlr",
        description="multi-llm-rotator: Manage and rotate multiple LLM accounts.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- add ---
    p_add = sub.add_parser("add", help="Add an account")
    p_add.add_argument("provider", help="Provider: gemini | claude | openai")
    p_add.add_argument("label", help="Unique label for this account")
    p_add.add_argument("--key", required=True, help="API key")
    p_add.add_argument("--model", required=True, help="Default model")

    # --- remove ---
    p_rm = sub.add_parser("remove", help="Remove an account")
    p_rm.add_argument("provider")
    p_rm.add_argument("label")

    # --- list ---
    p_list = sub.add_parser("list", help="List accounts")
    p_list.add_argument("provider", nargs="?", help="Filter by provider")

    # --- enable / disable ---
    p_en = sub.add_parser("enable", help="Enable an account")
    p_en.add_argument("provider")
    p_en.add_argument("label")

    p_dis = sub.add_parser("disable", help="Disable an account")
    p_dis.add_argument("provider")
    p_dis.add_argument("label")

    # --- clear-rate-limits ---
    p_clr = sub.add_parser("clear-rate-limits", help="Clear rate-limit flags")
    p_clr.add_argument("provider", nargs="?", help="Limit to provider")

    # --- chat ---
    p_chat = sub.add_parser("chat", help="Send a one-shot chat message")
    p_chat.add_argument("provider")
    p_chat.add_argument("message")
    p_chat.add_argument("--model", default=None, help="Override model")
    p_chat.add_argument(
        "--strategy",
        default="round-robin",
        choices=[s.value for s in RotationStrategy],
        help="Rotation strategy",
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    mgr = AccountManager()

    if args.command == "add":
        acc = mgr.add_account(
            provider=args.provider,
            label=args.label,
            api_key=args.key,
            model=args.model,
        )
        print(f"Added {acc.provider}/{acc.label} (model={acc.model})")

    elif args.command == "remove":
        ok = mgr.remove_account(args.provider, args.label)
        if ok:
            print(f"Removed {args.provider}/{args.label}")
        else:
            print(f"Account {args.provider}/{args.label} not found", file=sys.stderr)
            return 1

    elif args.command == "list":
        accounts = mgr.list_accounts(args.provider)
        if not accounts:
            print("No accounts found.")
        else:
            print(f"{'PROVIDER':<10} {'LABEL':<15} {'MODEL':<30} {'ENABLED':<8} {'STATUS'}")
            print("-" * 75)
            for acc in accounts:
                import time
                status = "available" if acc.is_available() else (
                    f"rate-limited ({acc.rate_limited_until - time.time():.0f}s)"
                )
                print(f"{acc.provider:<10} {acc.label:<15} {acc.model:<30} {str(acc.enabled):<8} {status}")

    elif args.command == "enable":
        ok = mgr.set_enabled(args.provider, args.label, True)
        print("Enabled" if ok else "Not found")

    elif args.command == "disable":
        ok = mgr.set_enabled(args.provider, args.label, False)
        print("Disabled" if ok else "Not found")

    elif args.command == "clear-rate-limits":
        mgr.clear_rate_limits(getattr(args, "provider", None))
        print("Rate limits cleared.")

    elif args.command == "chat":
        rotator = LLMRotator(
            strategy=RotationStrategy(args.strategy),
            account_manager=mgr,
        )
        try:
            response = rotator.chat(
                provider=args.provider,
                messages=[{"role": "user", "content": args.message}],
                model=args.model,
            )
            print(response)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
