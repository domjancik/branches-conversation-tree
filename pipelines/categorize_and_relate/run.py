#!/usr/bin/env python3
"""
Run categorize-and-relate pipeline using Ollama SDK (Python version).

Features:
- Loads and templates prompt.md
- Injects input text (from --input or stdin) into the prompt
- Optionally injects existing categories from a JSON file
- Simple {{KEY}} templating replacements and legacy <PASTE RAW TEXT HERE>
- Calls `ollama generate` with configurable model (default: gemma3:4b)
- --dry-run to preview the final prompt
- --output to save the model response to a file

Requires: Python 3.8+, Ollama installed and running locally, and the Python SDK (`pip install ollama`).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import ollama  # Python SDK
except ImportError as e:
    ollama = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_input_text(input_path: Optional[Path]) -> str:
    if input_path is not None:
        if not input_path.is_file():
            raise FileNotFoundError(f"Input path not found: {input_path}")
        return read_text(input_path)
    # Read from stdin if piped
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        return data
    raise ValueError("No input provided. Specify --input or pipe content via stdin.")


def load_template_vars(var_pairs: list[str], vars_json_path: Optional[Path]) -> Dict[str, str]:
    vars_map: Dict[str, str] = {}
    if vars_json_path is not None:
        if not vars_json_path.is_file():
            raise FileNotFoundError(f"Vars JSON not found: {vars_json_path}")
        obj = json.loads(read_text(vars_json_path))
        if not isinstance(obj, dict):
            raise ValueError("Vars JSON must be a flat object {key: value, ...}")
        for k, v in obj.items():
            vars_map[str(k)] = "" if v is None else str(v)
    for pair in var_pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --var format. Use key=value. Got: {pair}")
        k, v = pair.split("=", 1)
        vars_map[k] = v
    return vars_map


def render_template(template: str, vars_map: Dict[str, str]) -> str:
    rendered = template
    for k, v in vars_map.items():
        placeholder = f"{{{{{k}}}}}"
        # literal replacement for placeholder
        rendered = re.sub(re.escape(placeholder), v, rendered)
    return rendered


def build_categories_blocks(categories_json_raw: str) -> Tuple[str, Optional[str]]:
    """Return (json_raw, bullets_or_none). Best-effort bullets."""
    bullets = None
    try:
        parsed = json.loads(categories_json_raw)
        lines = []
        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                _id = item.get("id")
                label = item.get("category") or item.get("label") or item.get("name")
                desc = item.get("description") or item.get("summary")
                line = f"- [{_id}] {label}" if _id is not None else f"- {label}"
                if desc:
                    line += f": {desc}"
                lines.append(line)
        elif isinstance(parsed, dict):
            for key, val in parsed.items():
                if isinstance(val, dict):
                    label = val.get("category") or val.get("label") or val.get("name") or key
                    desc = val.get("description") or val.get("summary")
                else:
                    label = str(val)
                    desc = None
                line = f"- [{key}] {label}"
                if desc:
                    line += f": {desc}"
                lines.append(line)
        if lines:
            bullets = "\n".join(lines)
    except Exception:
        pass
    return categories_json_raw, bullets


def inject_into_prompt(prompt: str, input_text: str, categories_json_raw: Optional[str]) -> str:
    vars_map = {"RAW_TEXT": input_text}

    if categories_json_raw:
        cj, bullets = build_categories_blocks(categories_json_raw)
        vars_map["CATEGORIES_JSON"] = cj
        if bullets:
            vars_map["CATEGORIES_BULLETS"] = bullets

    rendered = render_template(prompt, vars_map)

    # Legacy placeholder fallback
    if "<PASTE RAW TEXT HERE>" in rendered:
        rendered = rendered.replace("<PASTE RAW TEXT HERE>", input_text)

    # If categories provided but no placeholders, append a section before Input:
    if categories_json_raw:
        has_json_ph = "{{CATEGORIES_JSON}}" in rendered
        has_bul_ph = "{{CATEGORIES_BULLETS}}" in rendered
        if not (has_json_ph or has_bul_ph):
            append = ("\nKnown categories (optional, provided by data source):\n" "```json\n" f"{categories_json_raw}\n" "```")
            # Try to place before the Input: block
            m = re.search(r"\nInput:\s*\n\"\"\"", rendered)
            if m:
                start = m.start()
                rendered = rendered[:start] + append + rendered[start:]
            else:
                rendered += append

    return rendered


def call_ollama(prompt_text: str, model: str, temperature: float, seed: int) -> Tuple[int, str]:
    if ollama is None:
        raise RuntimeError(
            "Ollama Python SDK not installed. Install with: pip install ollama"
        )
    # Use the SDK generate API with options
    try:
        resp = ollama.generate(
            model=model,
            prompt=prompt_text,
            options={
                "temperature": float(temperature),
                "seed": int(seed),
            },
        )
    except Exception as e:
        # Mirror the previous interface: nonzero code and captured output
        msg = f"ollama SDK call failed: {e}"
        return 1, msg
    # The SDK returns a GenerateResponse object with 'response' attribute
    if hasattr(resp, 'response'):
        text = resp.response
    elif isinstance(resp, dict):
        text = resp.get("response", "")
    else:
        text = str(resp)
    return 0, text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Categorize and relate pipeline (Ollama)")
    parser.add_argument("--input", type=Path, help="Path to input text file. If omitted, read from stdin.")
    parser.add_argument("--categories", type=Path, help="Optional path to categories JSON file.")
    parser.add_argument("--var", action="append", help="Templating variable as key=value. Can repeat.")
    parser.add_argument("--vars-json", type=Path, help="Path to JSON object for templating variables.")
    parser.add_argument("--model", default="gemma3:4b", help="Ollama model name.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism.")
    parser.add_argument("--output", type=Path, help="Write model response to this file.")
    parser.add_argument("--dry-run", action="store_true", help="Print final prompt and exit.")

    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    prompt_path = script_dir / "prompt.md"
    if not prompt_path.is_file():
        print(f"prompt.md not found at {prompt_path}", file=sys.stderr)
        return 2

    prompt_template = read_text(prompt_path)
    input_text = read_input_text(args.input)

    categories_raw = None
    if args.categories is not None:
        if not args.categories.is_file():
            print(f"Categories path not found: {args.categories}", file=sys.stderr)
            return 2
        categories_raw = read_text(args.categories)

    extra_vars = load_template_vars(args.var or [], args.vars_json)

    rendered = inject_into_prompt(prompt_template, input_text, categories_raw)
    if extra_vars:
        rendered = render_template(rendered, extra_vars)

    if args.dry_run:
        # Write to stdout exactly
        sys.stdout.write(rendered)
        return 0

    code, output = call_ollama(rendered, args.model, args.temperature, args.seed)
    if code != 0:
        print(f"ollama generate exited with code {code}. Output:\n{output}", file=sys.stderr)
        return code if isinstance(code, int) else 1

    # Attempt to extract clean JSON from the model output
    def _extract_clean_json(text: str) -> Optional[str]:
        t = text.strip()
        # 1) fenced block ```json ... ``` or ``` ... ```
        m = re.search(r"```(?:json)?\s*(.*?)```", t, flags=re.S | re.I)
        if m:
            candidate = m.group(1).strip()
            try:
                obj = json.loads(candidate)
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                pass
        # 2) raw JSON object substring fallback
        first = t.find("{")
        last = t.rfind("}")
        if first != -1 and last != -1 and last > first:
            candidate = t[first:last+1]
            try:
                obj = json.loads(candidate)
                return json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return None

    def _enhance_text_ranges(result_json: str, original_text: str) -> str:
        """Validate and enhance text ranges with fuzzy matching if needed."""
        try:
            data = json.loads(result_json)
            if "segments" not in data:
                return result_json
                
            for segment in data["segments"]:
                if "text_ranges" not in segment:
                    continue
                    
                for text_range in segment["text_ranges"]:
                    start_char = text_range.get("start_char")
                    end_char = text_range.get("end_char")
                    excerpt = text_range.get("excerpt", "")
                    
                    # Validate ranges are within bounds
                    if start_char is not None and end_char is not None:
                        start_char = max(0, min(start_char, len(original_text)))
                        end_char = max(start_char, min(end_char, len(original_text)))
                        text_range["start_char"] = start_char
                        text_range["end_char"] = end_char
                        
                        # Extract actual text at those positions
                        actual_text = original_text[start_char:end_char]
                        text_range["actual_text"] = actual_text
                        
                        # If excerpt doesn't match, try fuzzy search
                        if excerpt and excerpt.strip() not in actual_text:
                            # Simple fuzzy search for the excerpt in nearby text
                            search_start = max(0, start_char - 100)
                            search_end = min(len(original_text), end_char + 100)
                            search_area = original_text[search_start:search_end]
                            
                            # Find best match for excerpt in search area
                            excerpt_lower = excerpt.lower().strip()
                            best_pos = search_area.lower().find(excerpt_lower)
                            if best_pos != -1:
                                # Adjust ranges to actual found position
                                actual_start = search_start + best_pos
                                actual_end = actual_start + len(excerpt)
                                text_range["corrected_start_char"] = actual_start
                                text_range["corrected_end_char"] = actual_end
                                text_range["corrected_text"] = original_text[actual_start:actual_end]
            
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            # If enhancement fails, return original
            return result_json

    cleaned = _extract_clean_json(output)
    if cleaned is not None:
        # Enhance with text range validation
        enhanced = _enhance_text_ranges(cleaned, input_text)
        final_out = enhanced
    else:
        final_out = output

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(final_out, encoding="utf-8")
        print(f"Saved response to {args.output}")
    else:
        sys.stdout.write(final_out)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except BrokenPipeError:
        # Allow piping to head/tail without stack traces
        try:
            sys.stdout.close()
        finally:
            pass

