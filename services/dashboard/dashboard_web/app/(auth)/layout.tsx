import { AnimatedGridBg } from "@/components/layout/animated-grid-bg"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-neutral-950 dark relative overflow-hidden">
      <AnimatedGridBg />
      <div className="scan-line" />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
