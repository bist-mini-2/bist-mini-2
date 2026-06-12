import { redirect } from "next/navigation";

/**
 * 루트 경로(/)에 대응되는 페이지로, 진입 시 즉시 /feature1 경로로 리다이렉트합니다.
 */
export default function RootPage() {
  redirect("/feature1");
}
