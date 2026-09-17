import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate, useParams } from 'react-router'
import { Plus, LogOut, Users, ScrollText, Briefcase, FileText, MessageSquare } from 'lucide-react'
import { clearTokens } from '@/lib/token-storage'
import { listConversations, type ConversationSummary } from '@/api/conversations'
import { getMe } from '@/api/auth'
import { cn } from 'cn'

const NAV_ITEMS = [
  { to: '/', label: 'Чат', icon: MessageSquare, end: true },
  { to: '/candidates', label: 'CV кандидатів', icon: Users },
  { to: '/policies', label: 'HR-політики', icon: ScrollText },
  { to: '/job-requirements', label: 'Вакансії', icon: Briefcase },
  { to: '/reports', label: 'Звіти', icon: FileText },
]

function formatDisplayName(email: string): string {
  const localPart = email.split('@')[0]
  return localPart
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function getInitials(displayName: string): string {
  return displayName
    .split(' ')
    .map((part) => part.charAt(0))
    .join('')
    .toUpperCase()
}

export default function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { conversationId } = useParams<{ conversationId?: string }>()
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [userEmail, setUserEmail] = useState<string | null>(null)

  const isChatRoute = location.pathname === '/' || location.pathname.startsWith('/c/')

  useEffect(() => {
    if (!isChatRoute) return
    listConversations()
      .then(setConversations)
      .catch(() => {})
  }, [location.pathname, isChatRoute])

  useEffect(() => {
    getMe()
      .then((user) => setUserEmail(user.email))
      .catch(() => {})
  }, [])

  function handleLogout() {
    clearTokens()
    navigate('/login')
  }

  const displayName = userEmail ? formatDisplayName(userEmail) : 'Обліковий запис'

  return (
    <div className="flex h-screen w-full bg-background">
      <aside className="flex w-[260px] shrink-0 flex-col border-r border-border bg-muted px-4 py-6">
        <div className="flex items-center gap-2 px-1">
          <img src="/logo.png" alt="" className="size-7 shrink-0 rounded-full" />
          <div className="font-heading text-xl font-semibold italic text-foreground">Hirelume</div>
        </div>
        <div className="px-1 pb-5 pl-9 pt-0.5 text-[11.5px] font-medium text-muted-foreground">
          People Analytics
        </div>

        <button
          onClick={() => navigate('/')}
          className="mb-5 flex cursor-pointer items-center gap-2.5 rounded-lg border border-primary px-3 py-2.5 text-[13.5px] font-medium text-primary transition-colors hover:bg-primary/5"
        >
          <Plus className="size-4" />
          Нова розмова
        </button>

        <div className="flex flex-1 flex-col overflow-hidden">
          <nav className="flex shrink-0 flex-col gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-[13.5px] font-medium text-muted-foreground transition-colors hover:bg-accent/60',
                    (isActive || (to === '/' && isChatRoute)) && 'bg-accent text-accent-foreground',
                  )
                }
              >
                <Icon className="size-4" />
                {label}
              </NavLink>
            ))}
          </nav>

          {isChatRoute && (
            <div className="mt-5 flex flex-1 flex-col overflow-y-auto border-t border-border pt-4">
              <div className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Розмови
              </div>
              {conversations.map((c) => (
                <NavLink
                  key={c.id}
                  to={`/c/${c.id}`}
                  className={cn(
                    'truncate rounded-lg px-3 py-2.5 text-left text-[13.5px] text-muted-foreground transition-colors hover:bg-accent/60',
                    c.id === conversationId && 'bg-accent font-medium text-accent-foreground',
                  )}
                >
                  {c.title}
                </NavLink>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2.5 border-t border-border pt-4">
          <div className="flex size-[30px] shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
            {userEmail ? getInitials(displayName) : '…'}
          </div>
          <div className="min-w-0 flex-1 truncate text-[12.5px] font-medium text-foreground">
            {displayName}
          </div>
          <button onClick={handleLogout} aria-label="Вийти" className="shrink-0 cursor-pointer text-muted-foreground hover:text-foreground">
            <LogOut className="size-[15px]" />
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}
