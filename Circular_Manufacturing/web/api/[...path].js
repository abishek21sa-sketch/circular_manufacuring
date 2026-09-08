export default async function handler(req, res) {
  const backend = (process.env.CIRCULAR_BACKEND_URL || "").replace(/\/$/, "");
  const token = process.env.CIRCULAR_API_TOKEN || "";
  if (!backend || !token) {
    res.status(503).json({
      error: "Vercel proxy is not configured",
      required: ["CIRCULAR_BACKEND_URL", "CIRCULAR_API_TOKEN"],
    });
    return;
  }
  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }
  const path = Array.isArray(req.query.path) ? req.query.path.join("/") : req.query.path || "";
  const query = new URL(req.url, "https://vercel.invalid").search;
  const body = req.body && typeof req.body !== "string" ? JSON.stringify(req.body) : req.body;
  const upstream = await fetch(`${backend}/${path}${query}`, {
    method: req.method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": req.headers["content-type"] || "application/json",
    },
    body: ["GET", "HEAD"].includes(req.method) ? undefined : body,
  });
  const body = await upstream.arrayBuffer();
  res.status(upstream.status);
  res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.send(Buffer.from(body));
}
