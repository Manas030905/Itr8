import { cookies } from "next/headers";
import createClient from "openapi-fetch";
import type { paths } from "./schema";

/** Typed API client for server components. Forwards the visitor's cookies to FastAPI. */
export async function serverApi() {
  const cookieHeader = (await cookies()).toString();
  return createClient<paths>({
    baseUrl: process.env.API_INTERNAL_URL ?? "http://localhost:8000",
    headers: { cookie: cookieHeader },
    cache: "no-store",
  });
}
