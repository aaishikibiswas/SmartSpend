import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_ROUTES = new Set(["/login", "/register"]);
const PROTECTED_PATHS = ["/profile", "/settings", "/simulator"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/_next") || pathname.startsWith("/api") || pathname.includes(".")) {
    return NextResponse.next();
  }

  const hasSession = Boolean(request.cookies.get("smartspend_session")?.value);
  const isProtected = PROTECTED_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));

  if (!hasSession && isProtected) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (!hasSession && !PUBLIC_ROUTES.has(pathname)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (hasSession && PUBLIC_ROUTES.has(pathname)) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
