import { Outlet, NavLink, Link } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Download,
  Settings,
  Newspaper,
  Mail,
  FlaskConical,
  Sparkles,
  Briefcase,
  Heart,
  Cpu,
  Globe,
  Rss,
  Calendar,
  Radio,
} from 'lucide-react'
import clsx from 'clsx'
import { useBranding } from '../contexts/BrandingContext'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/pulse', icon: Radio, label: 'Live Pulse' },
  { to: '/fetch', icon: Download, label: 'Fetch Papers' },
  { to: '/papers', icon: FileText, label: 'Papers' },
  { to: '/digests', icon: Newspaper, label: 'Digests' },
  { to: '/schedules', icon: Calendar, label: 'Schedules' },
  { to: '/newsletters', icon: Mail, label: 'Newsletters' },
  { to: '/sources', icon: Rss, label: 'Sources' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

// Map domain IDs to icons
const domainIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  science: FlaskConical,
  tech: Cpu,
  business: Briefcase,
  health: Heart,
  news: Globe,
}

export default function Layout() {
  const { branding, activeDomainId } = useBranding()

  // Get the appropriate icon for the active domain
  const DomainIcon = activeDomainId ? (domainIcons[activeDomainId] || FlaskConical) : FlaskConical

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-ink-900 border-r border-ink-800 flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-6 border-b border-ink-800">
          <Link to="/" className="flex items-center gap-3 group">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg"
              style={{
                background: `linear-gradient(to bottom right, ${branding?.primary_color || '#0984e3'}, ${branding?.secondary_color || '#6c5ce7'})`,
                boxShadow: `0 10px 15px -3px ${branding?.primary_color || '#0984e3'}30`,
              }}
            >
              <DomainIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display text-lg font-semibold text-ink-50 group-hover:text-science-400 transition-colors">
                {branding?.app_name || 'Science Digest'}
              </h1>
              <p className="text-xs text-ink-500">{branding?.tagline || 'Research Aggregator'}</p>
            </div>
          </Link>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => clsx(
                'flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-all duration-200',
                isActive
                  ? 'bg-science-600/20 text-science-400 border border-science-600/30'
                  : 'text-ink-400 hover:text-ink-100 hover:bg-ink-800'
              )}
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        
        {/* Footer */}
        <div className="p-4 border-t border-ink-800">
          <div className="flex items-center gap-2 text-xs text-ink-500">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Research Insights</span>
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 ml-64">
        <div className="min-h-screen p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
