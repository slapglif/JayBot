export async function onRequest() {
  const upstream = new URL("https://kitty-litter-live.cryptsmith.workers.dev/api/live?weekend=1");
  const response = await fetch(upstream, { headers: { accept: "application/json" }, cf: { cacheTtl: 0, cacheEverything: false } });
  return new Response(response.body, { status: response.status, headers: { "content-type": response.headers.get("content-type") || "application/json; charset=utf-8", "cache-control": "no-store, no-cache, must-revalidate" } });
}
