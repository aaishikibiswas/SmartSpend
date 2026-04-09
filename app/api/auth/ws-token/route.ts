import { NextResponse } from "next/server";
import { getSessionToken } from "@/lib/auth-session";

export async function GET() {
  const token = await getSessionToken();

  if (!token) {
    return NextResponse.json({ message: "Authentication required." }, { status: 401 });
  }

  return NextResponse.json({
    status: 200,
    data: {
      token,
    },
  });
}
