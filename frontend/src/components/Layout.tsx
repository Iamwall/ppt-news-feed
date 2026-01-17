import { Outlet, NavLink, Link } from 'react-router-dom'
import { 
  LayoutDashboard, 
  FileText, 
  Download, 
  Settings, 
  Newspaper,
  Mail,
  FlaskConical,
  Sparkles
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/fetch', icon: Download, label: 'Fetch Papers' },
  { to: '/papers', icon: FileText, label: 'Papers' },
  { to: '/digests', icon: Newspaper, label: 'Digests' },
  { to: '/newsletters', icon: Mail, label: 'Newsletters' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-ink-900 border-r border-ink-800 flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-6 border-b border-ink-800">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-science-500 to-science-700 flex items-center justify-center shadow-lg shadow-science-600/30">
              <FlaskConical className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display text-lg font-semibold text-ink-50 group-hover:text-science-400 transition-colors">
                Science Digest
              </h1>
              <p className="text-xs text-ink-500">Research Aggregator</p>
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
