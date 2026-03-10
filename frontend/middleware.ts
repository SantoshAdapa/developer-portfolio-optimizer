import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const apiKey = process.env.API_KEY;
  if (apiKey) {
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("X-API-Key", apiKey);
    return NextResponse.next({
      request: { headers: requestHeaders },
    });
  }
  return NextResponse.next();
}

export const config = {
  matcher: "/api/:path*",
};
