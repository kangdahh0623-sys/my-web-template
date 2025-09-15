import Link from "next/link";
import AppShell from "@/components/layout/AppShell";

export default function HomePage() {
  return (
    <AppShell>
      <div className="space-y-4 max-w-3xl">
        <h1 className="text-3xl font-bold">급식줍쇼</h1>
        <p className="text-gray-600">
          학생: 전/후 사진 업로드 → 섭취량/영양 확인, 리뷰 남기기<br />
          영양사: 데이터·물가 반영 식단표 생성/공유
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/student" className="px-4 py-2 rounded-xl bg-blue-600 text-white">
            식단 분석·영양
          </Link>
          <Link href="/nutritionist" className="px-4 py-2 rounded-xl bg-emerald-600 text-white">
            영양사·식단표
          </Link>
        </div>
      </div>
    </AppShell>
  );
}
