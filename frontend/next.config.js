/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Standalone output for Docker (copies only production dependencies)
  output: 'standalone',

  // ── NO rewrites needed ────────────────────────────────────────────────────
  // frontend/lib/api.ts constructs full absolute URLs using NEXT_PUBLIC_API_URL
  // (e.g. http://localhost:8000/api/v1/...) and fetches them directly from the
  // browser.  A Next.js rewrite only fires for requests proxied through the
  // Next.js *server* — it has no effect on browser-side fetch() calls that
  // already include the full host.
  //
  // Keeping a rewrite rule for /api/:path* also caused a conflict: when
  // NEXT_PUBLIC_API_URL was undefined at build time the destination became
  // "undefined/api/:path*", which broke every route starting with /api/.
};

module.exports = nextConfig;