const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await page.goto(`file:///${path.resolve("docs/demo/thumbnail.html").replace(/\\/g, "/")}`);
  await page.screenshot({ path: "build/video/good-neighbor-thumbnail.png" });
  await browser.close();
  console.log(path.resolve("build/video/good-neighbor-thumbnail.png"));
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
