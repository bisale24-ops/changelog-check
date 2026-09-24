"""Three blocks, always all three, and an exit code a CI job can act on."""
import html as html_module

GREEN, AMBER, GREY, BOLD, OFF = "\033[32m", "\033[33m", "\033[90m", "\033[1m", "\033[0m"

EXIT_OK = 0
EXIT_UNSUPPORTED = 1
EXIT_UNMENTIONED = 2
EXIT_BROKEN = 3


def describe(commit):
    files = ", ".join(commit.files[:3]) + (f" +{len(commit.files) - 3} more" if len(commit.files) > 3 else "")
    return f"{commit.sha[:8]}  {commit.subject}" + (f"\n        {files}" if files else "")


def render_terminal(result, colour=True):
    def paint(text, code):
        return f"{code}{text}{OFF}" if colour else text

    lines = []
    supported = [r for r in result["claims"] if r["verdict"]["supported"]]
    unsupported = [r for r in result["claims"] if not r["verdict"]["supported"]]

    lines.append(paint("SUPPORTED", BOLD) + f"  {len(supported)} of {len(result['claims'])} claims")
    for item in supported:
        lines.append(paint(f"  ✓ {item['claim']}", GREEN))
        for commit, found in item["verdict"]["hits"][:3]:
            why = ", ".join(f"{kind} {value}" for kind, value in found[:3])
            lines.append(paint(f"      {describe(commit)}", GREY))
            lines.append(paint(f"        matched on {why}", GREY))
    if not supported:
        lines.append(paint("  nothing in the notes could be tied to a commit", GREY))

    lines.append("")
    lines.append(paint("SHIPPED WITHOUT A MENTION", BOLD) + f"  {len(result['unmentioned'])} commits")
    for commit in result["unmentioned"][:12]:
        lines.append(paint(f"  ? {describe(commit)}", AMBER))
        lines.append(paint(f"        +{commit.insertions} −{commit.deletions}", GREY))
    if not result["unmentioned"]:
        lines.append(paint("  every substantial commit is covered by a claim", GREY))

    lines.append("")
    lines.append(paint("NO EVIDENCE FOUND", BOLD) + f"  {len(unsupported)} claims")
    for item in unsupported:
        lines.append(paint(f"  ✗ {item['claim']}", AMBER))
        looked = item["searched"]
        lines.append(paint(f"        looked for {looked or 'nothing concrete in this line'}", GREY))
    if not unsupported:
        lines.append(paint("  every claim rests on something in the diff", GREY))

    lines.append("")
    lines.append(paint(f"{result['range']}: {len(result['commits'])} commits, "
                       f"{result['insertions']} insertions, {result['deletions']} deletions", GREY))
    if result.get("shallow"):
        lines.append(paint("  the clone is shallow, so older commits are invisible: "
                           "git fetch --unshallow", AMBER))
    lines.append(paint("Evidence is git history. A claim about behaviour this cannot see "
                       "is reported as unverified, not as false.", GREY))
    return "\n".join(lines)


def exit_code(result, strict=False):
    if result.get("broken"):
        return EXIT_BROKEN
    if any(not r["verdict"]["supported"] for r in result["claims"]):
        return EXIT_UNSUPPORTED
    if strict and result["unmentioned"]:
        return EXIT_UNMENTIONED
    return EXIT_OK


def render_html(result):
    esc = html_module.escape
    rows = []
    for item in result["claims"]:
        ok = item["verdict"]["supported"]
        evidence = "".join(
            f"<div class=e><code>{esc(commit.sha[:8])}</code> {esc(commit.subject)}"
            f"<span class=w>{esc(', '.join(f'{k} {v}' for k, v in found[:3]))}</span></div>"
            for commit, found in item["verdict"]["hits"][:3])
        rows.append(f"<li class={'ok' if ok else 'no'}><b>{esc(item['claim'])}</b>{evidence}"
                    + ("" if ok else f"<div class=w>looked for {esc(item['searched'])}</div>") + "</li>")
    silent = "".join(
        f"<li class=no><b>{esc(c.subject)}</b><div class=w><code>{esc(c.sha[:8])}</code> "
        f"+{c.insertions} −{c.deletions} · {esc(', '.join(c.files[:3]))}</div></li>"
        for c in result["unmentioned"][:20])
    return f"""<!doctype html><meta charset=utf-8><title>Changelog check — {esc(result['range'])}</title>
<style>
 :root {{ --bg:#fbfaf7; --fg:#1a1a18; --muted:#6b6a64; --line:#e2e0d8; --ok:#2f6f45; --no:#8a5a12; }}
 @media (prefers-color-scheme: dark) {{ :root:not([data-theme=light]) {{
   --bg:#14140f; --fg:#eceae2; --muted:#9a988e; --line:#2c2b24; --ok:#7fc79a; --no:#e0b063; }} }}
 body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 system-ui,sans-serif; }}
 .wrap {{ max-width:820px; margin:0 auto; padding:32px 16px 72px; }}
 h1 {{ font-size:24px; margin:0 0 4px; }} .sub {{ color:var(--muted); margin:0 0 28px; }}
 h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.08em; margin:30px 0 10px; }}
 ul {{ list-style:none; padding:0; margin:0; }}
 li {{ border:1px solid var(--line); border-left-width:3px; border-radius:10px; padding:12px 14px;
       margin-bottom:8px; background:color-mix(in srgb, var(--bg) 80%, #fff); }}
 li.ok {{ border-left-color:var(--ok); }} li.no {{ border-left-color:var(--no); }}
 .e {{ margin-top:8px; font-size:14px; color:var(--muted); }}
 .w {{ display:block; color:var(--muted); font-size:13px; }}
 code {{ font-family:ui-monospace,Menlo,monospace; }}
 footer {{ color:var(--muted); font-size:13px; margin-top:28px; border-top:1px solid var(--line); padding-top:12px; }}
</style><div class=wrap>
<h1>Does the release note tell the truth?</h1>
<p class=sub>{esc(result['range'])} · {len(result['commits'])} commits · +{result['insertions']} −{result['deletions']}</p>
<h2>Claims</h2><ul>{''.join(rows) or '<li class=no>no claims found in the notes</li>'}</ul>
<h2>Shipped without a mention</h2><ul>{silent or '<li class=ok>every substantial commit is covered</li>'}</ul>
<footer>Evidence is git history: issue numbers, flags, identifiers the diff defines and files it
touches. Shared ordinary words are not treated as evidence, so a claim about behaviour this
cannot see is reported as unverified rather than false.</footer></div>"""
