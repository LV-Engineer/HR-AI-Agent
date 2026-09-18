import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate, useParams } from 'react-router'
import { Plus, LogOut, Users, ScrollText, Briefcase, FileText, MessageSquare, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { clearTokens } from '@/lib/token-storage'
import { listConversations, deleteConversation, type ConversationSummary } from '@/api/conversations'
import { getMe } from '@/api/auth'
import { cn } from 'cn'
import ConfirmDialog from '@/components/ConfirmDialog'

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
  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(null)

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

  async function confirmDeleteConversation() {
    if (!deleteTarget) return
    try {
      await deleteConversation(deleteTarget.id)
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id))
      toast.success('Розмову видалено')
      if (deleteTarget.id === conversationId) {
        navigate('/')
      }
    } catch {
      toast.error('Не вдалося видалити розмову')
    } finally {
      setDeleteTarget(null)
    }
  }

  const displayName = userEmail ? formatDisplayName(userEmail) : 'Обліковий запис'

  return (
    <div className="flex h-screen w-full bg-background">
      <aside className="flex w-[260px] shrink-0 flex-col border-r border-border bg-muted px-4 py-6">
        <div className="flex items-center gap-2 px-1">
          <img src="/logo-transaparent.png" alt="" className="size-7 shrink-0" />
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
            <div className="mt-5 flex flex-1 flex-col gap-1 overflow-y-auto border-t border-border pt-4">
              <div className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Розмови
              </div>
              {conversations.length === 0 ? (
                <div className="px-3 py-2 text-[13px] text-muted-foreground">Ще немає розмов</div>
              ) : (
                conversations.map((c) => {
                  const isActive = c.id === conversationId
                  return (
                    <div
                      key={c.id}
                      className={cn(
                        'group flex items-center rounded-lg pr-1.5 transition-colors hover:bg-accent/60',
                        isActive && 'bg-accent',
                      )}
                    >
                      <NavLink
                        to={`/c/${c.id}`}
                        className={cn(
                          'min-w-0 flex-1 truncate px-3 py-2.5 text-left text-[13.5px]',
                          isActive ? 'font-medium text-accent-foreground' : 'text-muted-foreground',
                        )}
                      >
                        {c.title}
                      </NavLink>
                      <button
                        onClick={(e) => {
                          e.preventDefault()
                          setDeleteTarget(c)
                        }}
                        aria-label={`Видалити розмову ${c.title}`}
                        className="shrink-0 cursor-pointer p-1 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </div>
                  )
                })
              )}
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

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Видалити розмову?"
        description={deleteTarget ? `Розмову "${deleteTarget.title}" буде видалено безповоротно.` : ''}
        onConfirm={confirmDeleteConversation}
      />
    </div>
  )
}
