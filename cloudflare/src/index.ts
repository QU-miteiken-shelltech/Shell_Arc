import { AwsClient } from "aws4fetch";
import { DurableObject } from "cloudflare:workers";

interface Env {
  BUCKET: R2Bucket;
  LOCK: DurableObjectNamespace<LockDO>;
  R2_ACCESS_KEY_ID: string;
  R2_SECRET_ACCESS_KEY: string;
  R2_ACCOUNT_ID: string;
  R2_BUCKET_NAME: string;
  ALLOWED_ORIGIN: string;
  API_TOKEN: string;
}

const PUT_EXPIRES_SEC = 300;
const GET_EXPIRES_SEC = 300;

// AUTH
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
    if (pathname.startsWith("/lock/")) return lockHandler(req, env, userId, pathname.slice(6));
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
  const key = body?.key ?? `uploads/${userId}/${crypto.randomUUID()}.${ext}`;

  const url = await signUrl(
    env, 
    "PUT", 
    key, 
    {
      expires: PUT_EXPIRES_SEC,
      contentType,
    }
  );

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

// DO

interface LockRecord {
  token: string;
  owner: string;
  acquiredAt: number;
  expiresAt: number;
  metadata: Record<string, unknown>;
}

type PublicLock = Omit<LockRecord, "token">;

export class LockDO extends DurableObject<Env> {
  // 期限切れなら削除して null を返す (Alarm が遅れても正しく動く)
  private async current(): Promise<LockRecord | null> {
    const rec = await this.ctx.storage.get<LockRecord>("lock");
    if (!rec) return null;
    if (rec.expiresAt <= Date.now()) {
      await this.ctx.storage.delete("lock");
      return null;
    }
    return rec;
  }

  private toPublic(rec: LockRecord): PublicLock {
    const { token: _t, ...rest } = rec;
    return rest;
  }

  // ロックをかける
  async acquire(owner: string, ttlSec: number, metadata: Record<string, unknown>) {
    const cur = await this.current();
    if (cur) return { ok: false as const, holder: this.toPublic(cur) };

    const now = Date.now();
    const rec: LockRecord = {
      token: crypto.randomUUID(),
      owner,
      acquiredAt: now,
      expiresAt: now + ttlSec * 1000,
      metadata,
    };
    await this.ctx.storage.put("lock", rec);
    await this.ctx.storage.setAlarm(rec.expiresAt); // 失効予約
    return { ok: true as const, token: rec.token, lock: this.toPublic(rec) };
  }

  // ロックの有無
  async status() {
    return { locked: (await this.current()) !== null };
  }

  // メタデータ取得
  async info() {
    const cur = await this.current();
    if (!cur) return { locked: false as const };
    return {
      locked: true as const,
      ...this.toPublic(cur),
      remainingMs: cur.expiresAt - Date.now(),
    };
  }

  // ロックを外す (token 一致が必要)
  async release(token: string) {
    const cur = await this.current();
    if (!cur) return { ok: true as const, released: false }; // 既に無い = 冪等に成功
    if (cur.token !== token) return { ok: false as const };
    await this.ctx.storage.delete("lock");
    await this.ctx.storage.deleteAlarm();
    return { ok: true as const, released: true };
  }

  // 一定時間後の失効
  async alarm() {
    const rec = await this.ctx.storage.get<LockRecord>("lock");
    if (!rec) return;
    if (rec.expiresAt <= Date.now()) {
      await this.ctx.storage.delete("lock");
    } else {
      await this.ctx.storage.setAlarm(rec.expiresAt); // 早く起きた場合は再予約
    }
  }
}

const LOCK_NAME_RE = /^[A-Za-z0-9._:-]{1,128}$/;
const MAX_META_BYTES = 4096;

async function lockHandler(
  req: Request, env: Env, userId: string, action: string
): Promise<Response> {
  const body = await req
    .json<{
      name?: string;
      ttlSec?: number;
      metadata?: Record<string, unknown>;
      token?: string;
    }>()
    .catch(() => null);

  const name = body?.name ?? "";
  if (!LOCK_NAME_RE.test(name)) return json(env, { error: "invalid name" }, 400);

  const stub = env.LOCK.get(env.LOCK.idFromName(name));

  switch (action) {
    case "acquire": {
      const ttl = Math.min(Math.max(Math.floor(body?.ttlSec ?? 60), 1), 3600);
      const metadata = body?.metadata ?? {};
      if (JSON.stringify(metadata).length > MAX_META_BYTES) {
        return json(env, { error: "metadata too large" }, 400);
      }
      const r = await stub.acquire(userId, ttl, metadata);
      return r.ok ? json(env, r) : json(env, { error: "locked", holder: r.holder }, 409);
    }
    case "status":
      return json(env, await stub.status());
    case "info":
      return json(env, await stub.info());
    case "release": {
      if (!body?.token) return json(env, { error: "token required" }, 400);
      const r = await stub.release(body.token);
      return r.ok ? json(env, r) : json(env, { error: "invalid token" }, 403);
    }
    default:
      return json(env, { error: "not found" }, 404);
  }
}