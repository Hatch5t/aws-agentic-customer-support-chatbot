#!/usr/bin/env python3
"""Chat with your support chatbot from the terminal.

    python chat.py

Every run starts ONE conversation (one `runtimeSessionId`). The harness is
stateful: as long as you reuse the same session id, it remembers the whole
conversation — that is what lets it collect bug details over several turns.
Start the script again to get a fresh conversation.

The script attaches your AgentCore Gateway to each invoke, so the model can
call the create_bug_report tool. When it does, you'll see a line like:

    [tool call] bugreports___create_bug_report

Type your message and press Enter. Type 'quit' (or Ctrl-C) to exit.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.eventstream import EventStream


def event_stream(response):
    """Locate the streaming part of the invoke_harness response."""
    for value in response.values():
        if isinstance(value, EventStream):
            return value
    raise RuntimeError(f"No event stream in response: {list(response)}")


def invoke(rt, config, session_id, user_text, verbose=False):
    """Send one user message; print the reply as it streams in.

    Returns the assistant's final text. Tool calls and tool results are
    handled server-side by the harness — we only watch them go by.
    """
    response = rt.invoke_harness(
        harnessArn=config["harness_arn"],
        runtimeSessionId=session_id,
        # Pin the model on every invoke as well (belt and suspenders —
        # create_harness.py already pinned it on the harness).
        model={"bedrockModelConfig": {"modelId": config.get("model_id", "us.amazon.nova-pro-v1:0")}},
        # Attach the gateway so the model can use create_bug_report.
        tools=[{
            "type": "agentcore_gateway",
            "name": "support_gateway",
            "config": {"agentCoreGateway": {"gatewayArn": config["gateway_arn"]}},
        }],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
    )

    texts = []      # completed assistant messages
    buffer = []     # text of the message currently streaming
    for event in event_stream(response):
        if verbose:
            print(f"\n[event] {json.dumps(event, default=str)}", file=sys.stderr)
        if "contentBlockStart" in event:
            tool_use = event["contentBlockStart"].get("start", {}).get("toolUse")
            if tool_use:
                print(f"\n[tool call] {tool_use.get('name', '?')}", flush=True)
        elif "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                print(delta["text"], end="", flush=True)
                buffer.append(delta["text"])
        elif "messageStop" in event:
            if buffer:
                texts.append("".join(buffer))
                buffer = []
    if buffer:
        texts.append("".join(buffer))
    print()
    return texts[-1] if texts else ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="agentcore_config.json",
                        help="Config file written by the setup scripts.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print every raw stream event (for debugging).")
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if "harness_arn" not in config:
        sys.exit("No harness in config yet — run create_harness.py first.")

    # Session ids must be at least 33 characters — a UUID plus a suffix.
    session_id = f"{uuid.uuid4()}-support-chat"

    rt = boto3.client(
        "bedrock-agentcore",
        region_name=config["region"],
        # Tool-using turns can take a while; don't let boto3 time out.
        config=Config(read_timeout=300, retries={"max_attempts": 1}),
    )

    print(f"Connected to harness {config.get('harness_name', '?')} "
          f"(session {session_id}).")
    print("Type a message, or 'quit' to exit.\n")

    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in ("quit", "exit"):
            break
        print("bot> ", end="", flush=True)
        invoke(rt, config, session_id, user_text, verbose=args.verbose)
        print()


if __name__ == "__main__":
    main()
