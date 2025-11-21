import fs from "fs";
import path from "path";
import sharp from "sharp";
import { icons } from "./src/index.js";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), ".");
const inputDir = path.join(root, "icons");
const outputDir = path.join(root, "png");

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

async function run() {
  for (const icon of icons) {
    const inputPath = path.join(root, icon.file);
    const outputPath = path.join(outputDir, `${path.basename(icon.file, ".svg")}.png`);
    const svg = fs.readFileSync(inputPath);
    await sharp(svg)
      .resize(1024, 1024, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(outputPath);
    console.log(`Generated ${outputPath}`);
  }
}

run().catch((err) => {
  console.error("Icon generation failed", err);
  process.exit(1);
});
