import { redirect } from "next/navigation";
import AuthCard from "@/components/auth/AuthCard";
import { getCurrentUser } from "@/lib/auth-session";

export default async function RegisterPage() {
  const user = await getCurrentUser();
  if (user) {
    redirect("/");
  }

  return <AuthCard mode="register" />;
}
