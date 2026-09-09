const fs = require("fs");
const path = require("path");

const playwrightPath = process.env.PLAYWRIGHT_MODULE;
if (!playwrightPath) throw new Error("PLAYWRIGHT_MODULE is required");
const { chromium } = require(playwrightPath);

const baseUrl = process.argv[2] || "http://127.0.0.1:8876";
const manifestPath = process.argv[3] || "build/video/manifest.json";
const outputDirectory = path.resolve(process.argv[4] || "build/video");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

const chapterNames = {
  opening: ["GOOD NEIGHBOR", "Safe multi-agent recovery when plans break"],
  boundary: ["01  THE SAFETY BOUNDARY", "Useful agents. Deterministic authority."],
  run: ["02  BREAK THE PLAN", "A real capacity-drop incident"],
  activity: ["03  SHOW THE WORK", "Auditable tool traces and state versions"],
  decisions: ["04  STOP AT AUTHORITY", "Feasible does not mean authorized"],
  approve: ["05  HUMAN APPROVAL", "Resume safely from persisted state"],
  results: ["06  MEASURE, DON'T CLAIM", "60 frozen-seed evaluation cases"],
  evidence: ["07  REAL AWS EVIDENCE", "Two IAM-authorized AgentCore invocations"],
  closing: ["GOOD NEIGHBOR", "Recover useful work. Preserve human judgment."],
};

async function showChapter(page, action) {
  const [title, subtitle] = chapterNames[action];
  await page.evaluate(({ title, subtitle, action }) => {
    document.querySelector("#video-chapter")?.remove();
    if (!document.querySelector("#video-polish-style")) {
      const style = document.createElement("style");
      style.id = "video-polish-style";
      style.textContent = `
        #video-chapter { position: fixed; left: 34px; top: 28px; z-index: 99999;
          max-width: 640px; padding: 14px 18px 13px; border-radius: 14px;
          color: #f8fafc; background: rgba(8, 15, 29, .90);
          border: 1px solid rgba(125, 211, 252, .35); box-shadow: 0 18px 48px rgba(2, 6, 23, .30);
          backdrop-filter: blur(14px); font-family: Inter, Segoe UI, sans-serif;
          animation: chapter-in .45s cubic-bezier(.2,.8,.2,1) both; }
        #video-chapter strong { display:block; color:#7dd3fc; font-size: 13px; letter-spacing: .14em; }
        #video-chapter span { display:block; margin-top:5px; font-size:20px; font-weight:650; letter-spacing:-.01em; }
        #video-chapter.hero { left:50%; top:50%; width:780px; max-width:calc(100vw - 120px); text-align:center;
          transform:translate(-50%,-50%); padding:42px 52px; background:rgba(8,15,29,.96); }
        #video-chapter.hero strong { font-size:29px; color:#fff; letter-spacing:.18em; }
        #video-chapter.hero span { margin-top:14px; color:#7dd3fc; font-size:25px; }
        @keyframes chapter-in { from { opacity:0; transform:translateY(-14px); } to { opacity:1; transform:translateY(0); } }
        #video-chapter.hero { animation-name: hero-in; }
        @keyframes hero-in { from { opacity:0; transform:translate(-50%,-46%) scale(.96); } to { opacity:1; transform:translate(-50%,-50%) scale(1); } }
      `;
      document.head.appendChild(style);
    }
    const card = document.createElement("div");
    card.id = "video-chapter";
    if (action === "opening" || action === "closing") card.className = "hero";
    card.innerHTML = `<strong>${title}</strong><span>${subtitle}</span>`;
    document.body.appendChild(card);
    window.setTimeout(
      () => document.querySelector("#video-chapter")?.remove(),
      action === "opening" || action === "closing" ? 3200 : 1900,
    );
  }, { title, subtitle, action });
}

async function pointAt(page, selector) {
  const box = await page.locator(selector).boundingBox();
  if (!box) throw new Error(`cannot focus missing element: ${selector}`);
  await page.evaluate(({ x, y }) => {
    let pointer = document.querySelector("#video-pointer");
    if (!pointer) {
      pointer = document.createElement("div");
      pointer.id = "video-pointer";
      pointer.style.cssText = `position:fixed;z-index:100000;width:20px;height:20px;border-radius:50%;
        background:#ff6b2c;border:3px solid #fff;box-shadow:0 0 0 8px rgba(255,107,44,.25),0 5px 18px rgba(8,15,29,.35);
        pointer-events:none;transition:left .55s cubic-bezier(.2,.8,.2,1),top .55s cubic-bezier(.2,.8,.2,1),opacity .2s;`;
      document.body.appendChild(pointer);
    }
    pointer.style.opacity = "1";
    pointer.style.left = `${x - 10}px`;
    pointer.style.top = `${y - 10}px`;
  }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
  await page.waitForTimeout(650);
}

async function pauseFor(page, segment) {
  const pointerLead = ["run", "activity", "decisions", "approve", "results"].includes(segment.action) ? 0.65 : 0;
  await page.waitForTimeout(Math.max(0, segment.duration_seconds + segment.gap_seconds - pointerLead) * 1000);
}

(async () => {
  fs.mkdirSync(outputDirectory, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: edge });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: outputDirectory, size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(async () => {
    await fetch("/api/actions/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key: `video-reset:${crypto.randomUUID()}` }),
    });
  });
  await page.reload({ waitUntil: "networkidle" });
  const video = page.video();

  for (const segment of manifest.segments) {
    if (segment.action === "evidence") {
      await page.goto(`${baseUrl}/evidence.html`, { waitUntil: "networkidle" });
    }
    await showChapter(page, segment.action);
    switch (segment.action) {
      case "opening":
        break;
      case "boundary":
        await page.locator(".boundary-panel").hover();
        break;
      case "run":
        await pointAt(page, "#start-button");
        await page.locator("#start-button").click();
        await page.waitForFunction(() => document.querySelector("#stage-pill")?.textContent === "Human decision");
        break;
      case "activity":
        await pointAt(page, '[data-view="activity"]');
        await page.locator('[data-view="activity"]').click();
        break;
      case "decisions":
        await pointAt(page, '[data-view="decisions"]');
        await page.locator('[data-view="decisions"]').click();
        break;
      case "approve":
        await pointAt(page, "#approve-button");
        await page.locator("#approve-button").click();
        await page.waitForFunction(() => document.querySelector("#stage-pill")?.textContent === "Recovered");
        break;
      case "results":
        await pointAt(page, '[data-view="operations"]');
        await page.locator('[data-view="operations"]').click();
        break;
      case "evidence":
        break;
      case "closing":
        break;
      default:
        throw new Error(`unsupported video action: ${segment.action}`);
    }
    await pauseFor(page, segment);
  }

  await page.close();
  await context.close();
  await browser.close();
  const originalPath = await video.path();
  const finalPath = path.join(outputDirectory, "good-neighbor-screen.webm");
  if (fs.existsSync(finalPath)) fs.unlinkSync(finalPath);
  fs.renameSync(originalPath, finalPath);
  console.log(JSON.stringify({ video: finalPath, duration_seconds: manifest.total_duration_seconds }));
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
