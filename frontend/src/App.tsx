import { Outlet, Link, useLocation, useNavigate } from '@tanstack/react-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { ScrollToPlugin } from 'gsap/ScrollToPlugin'
import { useGSAP } from '@gsap/react'
import { useRef, useEffect } from 'react'

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin, useGSAP)

export default function App() {
  const location = useLocation()
  const mainRef = useRef<HTMLDivElement>(null)
  const prevPath = useRef(location.pathname)

  useEffect(() => {
    if (prevPath.current === location.pathname) return
    prevPath.current = location.pathname

    const main = mainRef.current
    if (!main) return

    ScrollTrigger.getAll().forEach((t) => t.kill())
    gsap.to(window, { scrollTo: 0, duration: 0 })

    // Zoom through: new page rockets in from slightly small
    gsap.fromTo(
      main,
      { scale: 0.88, opacity: 0, filter: 'blur(12px)' },
      { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.65, ease: 'expo.out' }
    )
  }, [location.pathname])

  const isVyapa = location.pathname === '/vyapa'

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-500 ${isVyapa ? 'bg-white' : 'bg-[#0a0a0f]'}`}>
      <nav className={`relative z-30 flex items-center justify-between px-8 py-4 border-b transition-colors duration-500 ${
        isVyapa ? 'border-gray-200 bg-white' : 'border-[#1a1a2e] bg-[#0a0a0f]'
      }`}>
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="relative">
            <span className={`text-2xl font-bold tracking-tight transition-colors duration-500 ${
              isVyapa ? 'text-gray-400' : 'neon-cyan text-[#00f5ff]'
            }`}>ന്യായ</span>
            <span className={`text-2xl font-bold transition-colors duration-500 ${
              isVyapa ? 'text-gray-300' : 'text-[#e0e0ff]'
            }`}>-flow</span>
            <div className={`absolute -bottom-1 left-0 w-full h-px bg-gradient-to-r transition-opacity duration-500 ${
              isVyapa ? 'from-gray-300 to-gray-200' : 'from-[#00f5ff] to-[#bf00ff]'
            }`} />
          </div>
        </Link>

        <div className="flex items-center gap-6">
          <NavLink to="/" active={location.pathname === '/'}>
            Agent
          </NavLink>
          <NavLink to="/prompts" active={location.pathname === '/prompts'}>
            System Prompts
          </NavLink>
          <NavLink to="/transcript" active={location.pathname === '/transcript'}>
            Transcript
          </NavLink>
        </div>
      </nav>

      <main ref={mainRef} className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ to, active, children }: { to: string; active: boolean; children: React.ReactNode }) {
  const navigate = useNavigate()

  const handleClick = (e: React.MouseEvent) => {
    if (active) { e.preventDefault(); return }
    const main = document.querySelector('main')
    if (!main) return
    e.preventDefault()
    gsap.to(main, {
      scale: 1.08,
      opacity: 0,
      filter: 'blur(8px)',
      duration: 0.35,
      ease: 'expo.in',
      onComplete: () => { navigate({ to }) },
    })
  }

  return (
    <Link
      to={to}
      onClick={handleClick}
      className={`text-sm tracking-widest uppercase transition-all duration-300 no-underline ${
        active ? 'text-[#00f5ff] neon-cyan' : 'text-[#4a4a6a] hover:text-[#e0e0ff]'
      }`}
    >
      {children}
    </Link>
  )
}
