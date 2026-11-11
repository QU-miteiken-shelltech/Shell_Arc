import { AwsClient } from "aws4fetch";

interface Env {
  BUCKET: R2Bucket;
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
  R2_ACCOUNT_ID: string;
  R2_BUCKET_NAME: string;
  ALLOWED_ORIGIN: string;
  API_TOKEN: string;
}

const PUT_EXPIRES_SEC = 300;
const GET_EXPIRES_SEC = 300;

// ★ 認証スタブ: 本番では JWT 検証 / セッション / Cloudflare Access 等に置き換える
async function authenticate(req: Request, env: Env): Promise<string | null> {
  const auth = req.headers.get("Authorization");
  if (auth !== `Bearer ${env.API_TOKEN}`) return null;
  return "demo-user";
}

function cors(env: Env): HeadersInit {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function json(env: Env, body: unknown, status = 200): Response {
  return Response.json(body, { status, headers: cors(env) });
}

function isOwnKey(key: string, userId: string): boolean {
  return key.startsWith(`uploads/${userId}/`) && !key.includes("..");
}

async function signUrl(
  env: Env,
  method: "PUT" | "GET",
  key: string,
  opts: {
    expires: number;
    contentType?: string;                
    query?: Record<string, string>;       
  }
): Promise<string> {
  const client = new AwsClient({
    accessKeyId: env.R2_ACCESS_KEY_ID,
    secretAccessKey: env.R2_SECRET_ACCESS_KEY,
    service: "s3",
    region: "auto",
  });

  const target = new URL(
    `https://${env.R2_BUCKET_NAME}.${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${key}`
  );
  target.searchParams.set("X-Amz-Expires", String(opts.expires));
  for (const [k, v] of Object.entries(opts.query ?? {})) {
    target.searchParams.set(k, v); 
  }

  const headers: Record<string, string> = {};
  if (method === "PUT" && opts.contentType) headers["Content-Type"] = opts.contentType;

  const signed = await client.sign(new Request(target, { method, headers }), {
    aws: { signQuery: true, allHeaders: true },
  });
  return signed.url;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(req.url);

    if (req.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(env) });
    }
    if (req.method !== "POST") return json(env, { error: "not found" }, 404);

    const userId = await authenticate(req, env);
    if (!userId) return json(env, { error: "unauthorized" }, 401);

    if (pathname === "/upload/presign") return uploadPresign(req, env, userId);
    if (pathname === "/upload/complete") return uploadComplete(req, env, userId);
    if (pathname === "/download/presign") return downloadPresign(req, env, userId);
    return json(env, { error: "not found" }, 404);
  },
};

async function uploadPresign(req: Request, env: Env, userId: string): Promise<Response> {
  const body = await req
    .json<{ contentType?: string; ext?: string }>()
    .catch(() => null);

  const contentType = body?.contentType || "application/octet-stream";
  const rawExt = body?.ext ?? "";
  const ext = /^[a-z0-9]{1,10}$/i.test(rawExt) ? rawExt.toLowerCase() : "bin";
  const key = `uploads/${userId}/${crypto.randomUUID()}.${ext}`;

  const url = await signUrl(env, "PUT", key, {
    expires: PUT_EXPIRES_SEC,
    contentType,
  });

  return json(env, {
    key,
    url,
    method: "PUT",
    headers: { "Content-Type": contentType },
    expiresIn: PUT_EXPIRES_SEC,
  });
}

async function uploadComplete(req: Request, env: Env, userId: string): Promise<Response> {
  const body = await req.json<{ key?: string }>().catch(() => null);
  const key = body?.key ?? "";

  if (!isOwnKey(key, userId)) return json(env, { error: "forbidden" }, 403);

  const head = await env.BUCKET.head(key);
  if (!head) return json(env, { error: "object not found" }, 404);

  return json(env, {
    ok: true,
    key,
    size: head.size,
    contentType: head.httpMetadata?.contentType ?? "",
  });
}

async function downloadPresign(req: Request, env: Env, userId: string): Promise<Response> {
  const body = await req
    .json<{ key?: string; filename?: string }>()
    .catch(() => null);
  const key = body?.key ?? "";

  if (!isOwnKey(key, userId)) return json(env, { error: "forbidden" }, 403);

  const head = await env.BUCKET.head(key);
  if (!head) return json(env, { error: "object not found" }, 404);

  const safeName = (body?.filename ?? key.split("/").pop() ?? "download")
    .replace(/[^A-Za-z0-9._-]/g, "_")
    .slice(0, 100);

  const url = await signUrl(env, "GET", key, {
    expires: GET_EXPIRES_SEC,
    query: {
      "response-content-disposition": `attachment; filename="${safeName}"`,
    },
  });

  return json(env, {
    key,
    url,
    method: "GET",
    expiresIn: GET_EXPIRES_SEC,
  });
}