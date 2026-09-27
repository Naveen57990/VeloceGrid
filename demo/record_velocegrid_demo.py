"""
VeloceGrid: Automated 1080p Studio Demo Video Recorder
Generates natural TTS narration (en-US-AndrewNeural), renders synchronized in-DOM subtitle HUD,
and captures full interactive workflow on live production web console using Playwright.
"""

import os
import sys
import time
import json
import asyncio
import subprocess
from playwright.async_api import async_playwright

AUDIO_DIR = "/Users/naveen/Documents/antigravity/peaceful-fermi/velocegrid/demo/audio"
VIDEO_DIR = "/Users/naveen/Documents/antigravity/peaceful-fermi/velocegrid/demo"
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICE = "en-US-AndrewNeural"

SCENES = [
    {
        "id": "scene1",
        "text": "Autonomous agentic workflows often collapse under serial latency bottlenecks, black-box execution, and uncontrolled token burn. Introducing VeloceGrid, an open-source high-throughput agentic execution mesh and speculative verification engine powered by NVIDIA Nemotron on Nebius Token Factory.",
        "action": "intro"
    },
    {
        "id": "scene2",
        "text": "VeloceGrid compiles natural language instructions into directed acyclic dependency graphs, executing independent sub-tasks concurrently. Our speculative AST and schema verification gates validate intermediate code, JSON contracts, and SQL grammar before state propagation, slashing redundant token waste by over 41 percent.",
        "action": "dag_speculative"
    },
    {
        "id": "scene3",
        "text": "We leverage Nebius Token Factory's ultra-low latency infrastructure to dispatch across tiered NVIDIA models: Nemotron Mini 4B for rapid AST parsing, Nemotron 70B for speculative linting, and Nemotron-4-340B for high-precision algorithmic synthesis.",
        "action": "model_dispatch"
    },
    {
        "id": "scene4",
        "text": "The cyberdeck console provides a real-time interactive DAG canvas, live token throughput meters exceeding 2800 tokens per second, step-level cost ledgers, and one-click JSON topology exports. Complete with a 100 percent deterministic local test suite running in zero seconds.",
        "action": "console_telemetry"
    },
    {
        "id": "scene5",
        "text": "VeloceGrid brings industrial-grade predictability, speed, and cost efficiency to enterprise agentic systems. Open source, deterministic, and live today on Nebius AI Cloud.",
        "action": "conclusion"
    }
]

def generate_tts():
    print("[+] Generating TTS audio segments via edge-tts...")
    audio_files = []
    durations = []
    
    for i, s in enumerate(SCENES):
        audio_path = os.path.join(AUDIO_DIR, f"{s['id']}.mp3")
        cmd = ["edge-tts", "--voice", VOICE, "--text", s["text"], "--write-media", audio_path]
        subprocess.run(cmd, check=True)
        
        # Get duration with ffprobe
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ], capture_output=True, text=True, check=True)
        duration = float(probe.stdout.strip())
        s["duration"] = duration
        s["audio_path"] = audio_path
        print(f"  └─ Scene {i+1} duration: {duration:.2f}s")
    
    # Concatenate full audio
    concat_list_path = os.path.join(AUDIO_DIR, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for s in SCENES:
            f.write(f"file '{s['audio_path']}'\n")
            
    full_audio = os.path.join(VIDEO_DIR, "full_narration.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", full_audio
    ], check=True)
    
    total_dur = sum(s["duration"] for s in SCENES)
    print(f"[✔] Combined Narration Audio: {full_audio} ({total_dur:.2f}s)")
    return total_dur

async def record_video():
    total_duration = generate_tts()
    
    raw_video_dir = os.path.join(VIDEO_DIR, "raw_capture")
    os.makedirs(raw_video_dir, exist_ok=True)
    
    print("[+] Launching Playwright browser for 1080p recording...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=raw_video_dir,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Load live Vercel app
        target_url = "https://velocegrid.vercel.app"
        print(f"[+] Navigating to {target_url}...")
        await page.goto(target_url, wait_until="networkidle")
        await asyncio.sleep(1.0)
        
        # Inject Subtitle HUD
        await page.evaluate("""
            const hud = document.createElement('div');
            hud.id = 'hud-subtitle-box';
            hud.style.position = 'fixed';
            hud.style.bottom = '24px';
            hud.style.left = '50%';
            hud.style.transform = 'translateX(-50%)';
            hud.style.backgroundColor = 'rgba(8, 12, 20, 0.92)';
            hud.style.border = '1px solid rgba(6, 182, 212, 0.5)';
            hud.style.borderRadius = '14px';
            hud.style.padding = '12px 28px';
            hud.style.color = '#e2e8f0';
            hud.style.fontFamily = "'Plus Jakarta Sans', sans-serif";
            hud.style.fontSize = '17px';
            hud.style.fontWeight = '600';
            hud.style.letterSpacing = '0.01em';
            hud.style.textAlign = 'center';
            hud.style.maxWidth = '880px';
            hud.style.zIndex = '999999';
            hud.style.boxShadow = '0 10px 35px rgba(0,0,0,0.8), 0 0 20px rgba(6,182,212,0.3)';
            hud.style.pointerEvents = 'none';
            hud.style.backdropFilter = 'blur(10px)';
            hud.innerHTML = "<span style='color: #06b6d4;'>VELOCEGRID</span> • Deterministic Agentic Mesh on Nebius Token Factory";
            document.body.appendChild(hud);
        """)

        # Execute synchronized scenes
        for idx, scene in enumerate(SCENES):
            print(f"[+] Executing Scene {idx+1}: {scene['id']} ({scene['duration']:.2f}s)...")
            
            # Update Subtitle text
            text_escaped = scene["text"].replace("'", "\\'").replace('"', '\\"')
            await page.evaluate(f"""
                document.getElementById('hud-subtitle-box').innerHTML = "{text_escaped}";
            """)
            
            dur = scene["duration"]
            
            if scene["action"] == "intro":
                await asyncio.sleep(dur * 0.3)
                await page.evaluate("window.scrollTo({top: 100, behavior: 'smooth'})")
                await asyncio.sleep(dur * 0.7)
                
            elif scene["action"] == "dag_speculative":
                # Click execute refactor workflow
                await page.click("#btn-run")
                await asyncio.sleep(dur * 0.5)
                # Click on node cards
                await page.evaluate("document.querySelector('#node-card-optimize')?.click()")
                await asyncio.sleep(dur * 0.5)
                
            elif scene["action"] == "model_dispatch":
                # Switch to SQL optimizer workflow
                await page.click("#btn-wf-sql")
                await asyncio.sleep(1.2)
                await page.click("#btn-step")
                await asyncio.sleep(1.5)
                await page.click("#btn-step")
                await asyncio.sleep(dur - 2.7)
                
            elif scene["action"] == "console_telemetry":
                # Switch to research synthesis workflow
                await page.click("#btn-wf-research")
                await asyncio.sleep(1.0)
                await page.click("#btn-run")
                await asyncio.sleep(2.0)
                await page.evaluate("document.querySelector('#node-card-synthesize')?.click()")
                await asyncio.sleep(dur - 3.0)
                
            elif scene["action"] == "conclusion":
                await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
                await asyncio.sleep(dur)
        
        await asyncio.sleep(1.0)
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
    print(f"[✔] Raw Web Video captured at: {video_path}")
    
    # Merge video and audio with ffmpeg
    final_output = os.path.join(VIDEO_DIR, "velocegrid_demo.mp4")
    full_audio = os.path.join(VIDEO_DIR, "full_narration.mp3")
    
    print(f"[+] Merging 1080p video with AAC audio into {final_output}...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", full_audio,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_output
    ], check=True)
    
    print(f"[✔] FINAL 1080P DEMO VIDEO READY: {final_output}")

if __name__ == "__main__":
    asyncio.run(record_video())
