import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const backendUrl = process.env.API_URL || "http://localhost:8000";
  const destination = new URL(
    request.nextUrl.pathname + request.nextUrl.search,
    backendUrl
  );

  const headers = new Headers(request.headers);

  // Inject API key server-side so it's never exposed to the browser
  const apiKey = process.env.API_KEY;
  if (apiKey) {
    headers.set("X-API-Key", apiKey);
  }

  return NextResponse.rewrite(destination, {
    request: { headers },
  });
}

export const config = {
  matcher: "/api/:path*",
};
