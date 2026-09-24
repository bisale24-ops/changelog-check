"""Build the demo video: synthesised narration over real output.

    /tmp/ttsenv/bin/python video/build.py

Every terminal frame is the tool's actual output, captured into `shots/` by running it against
the public httpx repository and against this repository's own release notes. Nothing is retyped
for the camera. The narration is edge-tts; the last card says so.
"""
import asyncio
import pathlib
import re
import subprocess
import sys

from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
SHOTS = HERE / "shots"
BUILD = HERE / "build"
VOICE = "en-US-AndrewNeural"
W, H, FPS = 1280, 720, 30

SCENES = [
    ("card:title",
     "Every tool in this space writes release notes from the diff. That is the easy direction, "
     "and it is the one nobody checks. A generated note is trusted because a machine made it. A "
     "hand-written note is trusted because a person made it."),
    ("card:idea",
     "Changelog Check runs the other way. It takes the notes you already have and asks what "
     "evidence supports each line."),
    ("term:httpx-head",
     "Here it is on a real release of httpx, checked against that project's own changelog. "
     "Twelve of sixteen claims are supported by commits. Four changes shipped without a mention. "
     "Four lines have nothing behind them."),
    ("term:supported",
     "A supported claim shows its receipts: the commits, the files they touched, and what the "
     "match rested on — an identifier, a filename, an issue number."),
    ("term:noevidence",
     "And here are the lines the diff does not back. Note what the tool does not say. It does "
     "not call them false. A promise about a future API is not something git can see, so it is "
     "reported as unverified, and the search that was made is printed next to it."),
    ("card:evidence",
     "That distinction is the whole design. Shared ordinary English is not evidence. Improves "
     "the export, and a commit called tidy up exports, have a word in common and prove nothing. "
     "Evidence is an issue number, a flag, a filename, an identifier the diff defines. The rule "
     "misses real matches, and missing them is the acceptable failure — the cost of a false "
     "supported is a release note nobody checks again."),
    ("term:self",
     "It checks its own release notes too, in its own continuous integration, and exits non-zero "
     "when a claim has no evidence. One line in a workflow file fails the release before the "
     "notes are published."),
    ("card:limits",
     "What it cannot do is stated in the output rather than hidden. It reasons about lines and "
     "commits, not behaviour. A squashed history gives it less to work with, and it says so."),
    ("card:end",
     "Changelog Check. Receipts, silence, or nothing — and it tells you which. M I T licensed, "
     "and the narration in this video is synthesised."),
]

CARDS = {
    "title": """<h1>Who checks the release notes?</h1>
    <p class=sub>Every tool writes them from the diff. None of them reads the ones you have.</p>
    <pre>$ git log v1.2.0..v1.3.0 --oneline | wc -l
      47

$ wc -l &lt; CHANGELOG-1.3.0.md
       6</pre>""",
    "idea": """<h1>Changelog Check</h1>
    <p class=sub>Reads the notes you already have and asks what evidence supports each line.</p>
    <table>
      <tr><td class=ok>supported</td><td>these commits and these files do what the line says</td></tr>
      <tr><td class=no>shipped without a mention</td><td>a change went out and no line covers it</td></tr>
      <tr><td class=no>no evidence found</td><td>the line claims something the diff does not contain</td></tr>
    </table>
    <p class=foot>No dependencies, no network, no API key. The evidence is git on your machine.</p>""",
    "evidence": """<h1>What counts as evidence</h1>
    <table>
      <tr><th>signal</th><th>strength</th><th>example</th></tr>
      <tr><td>issue or PR number</td><td class=ok>strong</td><td>the line says (#412), a commit closes it</td></tr>
      <tr><td>command-line flag</td><td class=ok>strong</td><td><code>--strict</code> in the line and in the diff</td></tr>
      <tr><td>filename</td><td class=ok>strong</td><td>the line names <code>hours.py</code>, the commit touches it</td></tr>
      <tr><td>identifier</td><td>medium</td><td><code>verify=False</code> in the commit subject</td></tr>
      <tr><td>path fragment</td><td>weak</td><td>"export" and a commit in <code>export/</code></td></tr>
      <tr><td>a shared English word</td><td class=no>none</td><td>"improves" · "fixes" · "support"</td></tr>
    </table>""",
    "limits": """<h1>What it cannot do</h1>
    <table>
      <tr><td>Behaviour</td><td>"fixed the crash on startup" is matched against commits that touch
        startup, never against a test proving the crash is gone</td></tr>
      <tr><td>Squashed history</td><td>less evidence per line, and the report says that is what it
        is reading</td></tr>
      <tr><td>Weak matches</td><td>a path fragment can attach a plausible commit to an unrelated
        line; those are ranked last and labelled</td></tr>
    </table>
    <p class=foot>Stated in the output, not buried in a README.</p>""",
    "end": """<h1>Changelog Check</h1><p class=sub>Receipts, silence, or nothing — and it says which.</p>
    <p class=big>github.com/bisale24-ops/changelog-check</p>
    <p class=foot>MIT licensed · built with the Devpost Learn skill pack · 15 tests, no network ·
    the narration in this video is synthesised, there is no presenter.</p>""",
}

SHELL = {
    "httpx-head": ("$ changelog-check --repo httpx --from 0.27.2 --to 0.28.0 "
                   "--notes CHANGELOG.md --section 0.28.0", "httpx.txt", 0, 3),
    "supported": ("", "httpx.txt", 1, 12),
    "noevidence": ("", "httpx.txt", None, None),
    "self": ("$ changelog-check --from $(git rev-list --max-parents=0 HEAD) --to HEAD",
             "self.txt", None, None),
}

PAGE = """<!doctype html><meta charset=utf-8><style>
 body {{ margin:0; width:1280px; height:720px; background:#fbfaf7; color:#1a1a18;
   font:20px/1.5 system-ui,-apple-system,sans-serif; display:flex; flex-direction:column;
   justify-content:center; padding:0 64px; box-sizing:border-box; }}
 h1 {{ font-size:40px; margin:0 0 6px; letter-spacing:-.02em; }}
 .sub {{ color:#6b6a64; margin:0 0 26px; font-size:22px; }}
 table {{ border-collapse:collapse; font-size:19px; width:100%; }}
 td, th {{ text-align:left; padding:8px 12px; border-bottom:1px solid #e2e0d8; vertical-align:top; }}
 th {{ font-size:14px; text-transform:uppercase; letter-spacing:.06em; color:#6b6a64; }}
 .ok {{ color:#2f6f45; font-weight:600; }} .no {{ color:#8a5a12; font-weight:600; }}
 .big {{ font-size:28px; }} .foot {{ color:#6b6a64; font-size:16px; margin-top:22px; }}
 pre {{ font:17px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; background:#fff;
   border:1px solid #e2e0d8; border-left:3px solid #8a5a12; border-radius:10px;
   padding:16px 18px; margin:0; white-space:pre-wrap; }}
 code {{ font-family:ui-monospace,Menlo,monospace; }}
 .term {{ background:#14140f; color:#eceae2; border-radius:12px; padding:22px 24px;
   font:16px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace; white-space:pre-wrap;
   overflow:hidden; height:600px; box-sizing:border-box; }}
 .term b {{ color:#fff; }} .term .g {{ color:#7fc79a; }} .term .a {{ color:#e0b063; }}
 .term .d {{ color:#9a988e; }} .term .p {{ color:#7fc79a; }}
</style>{body}"""


def shell_html(command, source, start, end):
    text = (SHOTS / source).read_text().splitlines()
    if start is None:
        start = next(i for i, line in enumerate(text) if line.startswith("NO EVIDENCE"))
        end = start + 12
    body = []
    if command:
        body.append(f"<span class=p>$</span> <b>{command}</b>\n")
    for line in text[start:end]:
        escaped = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        if re.match(r"^(SUPPORTED|SHIPPED|NO EVIDENCE)", line):
            escaped = f"<b>{escaped}</b>"
        elif "✓" in line:
            escaped = f"<span class=g>{escaped}</span>"
        elif "✗" in line or "?" in line[:4]:
            escaped = f"<span class=a>{escaped}</span>"
        elif line.startswith("      ") or line.startswith("        "):
            escaped = f"<span class=d>{escaped}</span>"
        body.append(escaped)
    return f'<div class=term>{chr(10).join(body)}</div>'


def run(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


async def render_frames():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        for name, body in CARDS.items():
            await page.set_content(PAGE.format(body=body))
            await page.screenshot(path=str(BUILD / f"card-{name}.png"))
        for name, (command, source, start, end) in SHELL.items():
            await page.set_content(PAGE.format(body=shell_html(command, source, start, end)))
            await page.screenshot(path=str(BUILD / f"term-{name}.png"))
        await browser.close()


def narrate():
    for index, (_, line) in enumerate(SCENES):
        out = BUILD / f"line-{index:02d}.mp3"
        if not out.exists():
            subprocess.run([sys.executable.replace("python", "edge-tts"), "--voice", VOICE,
                            "--text", line, "--write-media", str(out)], check=True)


def main():
    BUILD.mkdir(exist_ok=True)
    asyncio.run(render_frames())
    narrate()
    segments = []
    for index, (frame, _) in enumerate(SCENES):
        kind, name = frame.split(":")
        image = BUILD / f"{'card' if kind == 'card' else 'term'}-{name}.png"
        audio = BUILD / f"line-{index:02d}.mp3"
        segment = BUILD / f"seg-{index:02d}.mp4"
        run("-loop", "1", "-i", str(image), "-i", str(audio),
            "-filter_complex",
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:0:color=0xfbfaf7,format=yuv420p[v];"
            f"[1:a]apad=pad_dur=0.8,aresample=48000[a]",
            "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-t", f"{duration(audio) + 0.8:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", str(segment))
        segments.append(segment)
    listing = BUILD / "segments.txt"
    listing.write_text("".join(f"file '{s.name}'\n" for s in segments))
    final = HERE / "changelog-check-demo.mp4"
    run("-f", "concat", "-safe", "0", "-i", str(listing),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        str(final))
    print(f"{final.name}  {duration(final):.1f}s")


if __name__ == "__main__":
    main()
