import createClient from "openapi-fetch";
import type { paths } from "./schema";

/** Typed API client for client components. Same-origin: /api/* is proxied to FastAPI. */
export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin" });
