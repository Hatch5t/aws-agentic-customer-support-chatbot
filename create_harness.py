#!/usr/bin/env python3
"""Create (or update) the AgentCore managed harness that runs your chatbot.

    python create_harness.py

What it does:
  1. Reads your system prompt from system_prompt.txt. If the file contains
     the placeholder {{FAQ}}, it is replaced with the contents of
     online_shop_faq.md — so you don't have to paste the FAQ by hand.
  2. Creates the harness with the model pinned to Amazon Nova Pro and your
     prompt as the system prompt. If a harness with the same name already
     exists, it is UPDATED instead — so iterating on your prompt is just:
     edit system_prompt.txt, re-run this script.
  3. Waits until the harness is READY (first creation takes ~2-3 minutes)
     and records the harness ARN in agentcore_config.json.

Note on the model: this course pins `us.amazon.nova-pro-v1:0` explicitly.
Do not rely on the harness default model — it requires an AWS Marketplace
subscription that lab accounts cannot complete. For reliable Nova tool
calling we also use greedy decoding (temperature 0, topK 1).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import boto3

FAQ_PLACEHOLDER = "{{FAQ}}"

# Greedy decoding (temperature 0 + topK 1) is AWS's recommendation for
# reliable tool calling with Nova models.
def model_config(model_id):
    return {
        "bedrockModelConfig": {
            "modelId": model_id,
            "temperature": 0.0,
            "additionalParams": {
                "additionalModelRequestFields": {
                    "inferenceConfig": {"topK": 1}
                }
            },
        }
    }


def load_prompt(prompt_path, faq_path):
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    if FAQ_PLACEHOLDER in prompt:
        faq = Path(faq_path).read_text(encoding="utf-8")
        prompt = prompt.replace(FAQ_PLACEHOLDER, faq)
    return prompt


def find_harness(acc, name):
    """Return the existing harness with this name, or None."""
    token = None
    while True:
        kwargs = {"nextToken": token} if token else {}
        page = acc.list_harnesses(**kwargs)
        for h in page.get("harnesses", []):
            if h.get("harnessName") == name:
                return h
        token = page.get("nextToken")
        if not token:
            return None


def wait_ready(acc, harness_id, timeout=360):
    """Poll until the harness is READY (or fails)."""
    deadline = time.time() + timeout
    status = "UNKNOWN"
    while time.time() < deadline:
        # get_harness nests everything under a top-level "harness" key.
        status = acc.get_harness(harnessId=harness_id)["harness"]["status"]
        if status == "READY":
            return status
        if status in ("FAILED", "DELETING"):
            sys.exit(f"Harness entered status {status} — check the AgentCore console.")
        print(f"  status: {status} — waiting...")
        time.sleep(15)
    sys.exit(f"Timed out waiting for the harness (last status: {status}).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="support_chatbot",
                        help="Harness name (letters, digits, underscores).")
    parser.add_argument("--prompt-file", default="system_prompt.txt",
                        help="File containing your system prompt.")
    parser.add_argument("--faq-file", default="online_shop_faq.md",
                        help="FAQ file substituted for {{FAQ}} in the prompt.")
    parser.add_argument("--model", default="us.amazon.nova-pro-v1:0",
                        help="Bedrock model id to pin.")
    parser.add_argument("--config", default="agentcore_config.json",
                        help="Config file written by setup_gateway.py.")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        sys.exit(f"{args.config} not found — run setup_gateway.py first.")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    prompt = load_prompt(args.prompt_file, args.faq_file)
    print(f"Loaded system prompt from {args.prompt_file} "
          f"({len(prompt)} characters).")

    acc = boto3.client("bedrock-agentcore-control", region_name=config["region"])

    existing = find_harness(acc, args.name)
    if existing:
        harness_id = existing.get("harnessId")
        print(f"Harness '{args.name}' already exists — updating its prompt/model...")
        # update_harness returns ConflictException while the harness is in a
        # transitional state (e.g. a previous run is still finishing) — wait
        # for it to settle first.
        if existing.get("status") in ("CREATING", "UPDATING"):
            print(f"  harness is still {existing['status']} — waiting for it "
                  "to settle before updating...")
            wait_ready(acc, harness_id)
        acc.update_harness(
            harnessId=harness_id,
            executionRoleArn=config["harness_execution_role_arn"],
            model=model_config(args.model),
            systemPrompt=[{"text": prompt}],
        )
    else:
        print(f"Creating harness '{args.name}' (takes ~2-3 minutes)...")
        # A freshly created execution role can take a few seconds to
        # propagate through IAM — retry a couple of times if needed.
        last_exc = None
        for attempt in range(3):
            try:
                harness = acc.create_harness(
                    harnessName=args.name,
                    executionRoleArn=config["harness_execution_role_arn"],
                    model=model_config(args.model),
                    systemPrompt=[{"text": prompt}],
                )
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                print(f"  create_harness failed ({exc}); retrying in 10s...")
                time.sleep(10)
        else:
            raise last_exc
        # create_harness (like get_harness) nests the details under "harness".
        harness_id = harness["harness"]["harnessId"]

    status = wait_ready(acc, harness_id)
    harness = acc.get_harness(harnessId=harness_id)["harness"]
    harness_arn = harness["arn"]

    config["harness_name"] = args.name
    config["harness_id"] = harness_id
    config["harness_arn"] = harness_arn
    config["model_id"] = args.model
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    print(f"\nHarness is {status}.")
    print(f"  harness arn: {harness_arn}")
    print(f"Saved to {args.config}. Try it out with:  python chat.py")


if __name__ == "__main__":
    main()
