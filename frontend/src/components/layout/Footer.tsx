// frontend/src/components/layout/Footer.tsx
export function Footer() {
  return (
    <footer className="bg-white border-t mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-gray-600">
          <p className="mb-2">
            © 2024 My Web Template. Made with FastAPI + Next.js
          </p>
          <p className="text-sm">
            {/* TODO: 추가 링크들 (개인정보처리방침, 이용약관 등) */}
            <a href="#" className="hover:text-blue-600 mx-2">GitHub</a>
            <a href="#" className="hover:text-blue-600 mx-2">Docs</a>
          </p>
        </div>
      </div>
    </footer>
  )
}