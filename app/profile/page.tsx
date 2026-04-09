import { Mail, ShieldCheck, Sparkles, UserCircle2 } from "lucide-react";
import { redirect } from "next/navigation";
import ProfileSettingsForm from "@/components/profile/ProfileSettingsForm";
import { getCurrentUser } from "@/lib/auth-session";

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className="space-y-8 py-8">
      <section className="rounded-[30px] border border-[#27314d] bg-[#0b1325]/90 p-8 shadow-[0_30px_90px_rgba(1,6,18,0.45)]">
        <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[#a3a6ff]">Profile</p>
        <div className="mt-4 flex flex-col gap-6 md:flex-row md:items-center">
          <img
            src={`https://i.pravatar.cc/150?u=${user.avatar_seed}`}
            alt={user.full_name}
            className="h-20 w-20 rounded-full border border-[#7277ff]/20"
          />
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-[#dee5ff]">{user.full_name}</h1>
            <p className="mt-2 text-sm text-[#a3aac4]">Your SmartSpend identity is connected across the sidebar, dashboard header, live alerts, and account session.</p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-[26px] border border-[#27314d] bg-[#10192d] p-6">
          <div className="flex items-center gap-3 text-[#dee5ff]">
            <UserCircle2 className="h-5 w-5 text-[#a3a6ff]" />
            <h2 className="text-lg font-bold">Account Name</h2>
          </div>
          <p className="mt-4 text-sm text-[#dee5ff]">{user.full_name}</p>
        </div>

        <div className="rounded-[26px] border border-[#27314d] bg-[#10192d] p-6">
          <div className="flex items-center gap-3 text-[#dee5ff]">
            <Mail className="h-5 w-5 text-[#a3a6ff]" />
            <h2 className="text-lg font-bold">Email</h2>
          </div>
          <p className="mt-4 text-sm text-[#dee5ff]">{user.email}</p>
        </div>

        <div className="rounded-[26px] border border-[#27314d] bg-[#10192d] p-6">
          <div className="flex items-center gap-3 text-[#dee5ff]">
            <ShieldCheck className="h-5 w-5 text-[#a3a6ff]" />
            <h2 className="text-lg font-bold">Plan</h2>
          </div>
          <p className="mt-4 text-sm text-[#dee5ff]">{user.plan}</p>
        </div>
      </section>

      <section className="rounded-[26px] border border-[#27314d] bg-[#10192d] p-6">
        <div className="flex items-center gap-3 text-[#dee5ff]">
          <Sparkles className="h-5 w-5 text-[#a3a6ff]" />
          <h2 className="text-lg font-bold">What&apos;s Connected</h2>
        </div>
        <ul className="mt-4 space-y-3 text-sm text-[#a3aac4]">
          <li>Your sidebar profile card reflects the signed-in user.</li>
          <li>Your dashboard header greets you by your first name.</li>
          <li>Your session persists with secure HTTP-only cookies until logout.</li>
          <li>Your WebSocket dashboard updates stay tied to your active session.</li>
        </ul>
      </section>

      <ProfileSettingsForm initialUser={user} />
    </div>
  );
}
