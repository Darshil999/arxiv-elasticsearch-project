import type { NextConfig } from "next";

// On Render, fail the build instead of shipping a site that calls http://localhost:8000.
if (process.env.RENDER && !process.env.NEXT_PUBLIC_API_URL) {
  throw new Error(
    "NEXT_PUBLIC_API_URL is not set. Add it in Render → your static site → Environment, then redeploy.",
  );
}

const nextConfig: NextConfig = {
  // The UI is a single client-rendered page that calls the FastAPI backend from the browser,
  // so it is exported as plain HTML/CSS/JS into `out/` and served by Render's free static-site CDN.
  output: "export",
};

export default nextConfig;
