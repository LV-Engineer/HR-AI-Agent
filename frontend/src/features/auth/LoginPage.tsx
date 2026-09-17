import { useState } from 'react'
import { useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { login } from '@/api/auth'
import { ApiError } from '@/api/client'
import { setTokens } from '@/lib/token-storage'

const loginSchema = z.object({
  email: z.string().min(1, "Вкажіть email").email('Некоректний формат email'),
  password: z.string().min(1, 'Вкажіть пароль'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  async function onSubmit(values: LoginFormValues) {
    setServerError(null)
    try {
      const tokens = await login(values.email, values.password)
      setTokens(tokens.access_token, tokens.refresh_token)
      navigate('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setServerError('Невірний email або пароль')
      } else {
        setServerError('Щось пішло не так. Спробуйте ще раз.')
      }
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="flex w-full max-w-[400px] flex-col items-center">
        <h1 className="mb-1.5 font-heading text-3xl font-semibold italic text-foreground">
          Hirelume
        </h1>
        <p className="mb-10 text-[13px] font-medium text-muted-foreground">People Analytics</p>

        {serverError && (
          <div className="mb-5.5 flex w-full items-center gap-2.5 rounded-[10px] border border-destructive/50 bg-destructive/10 px-4 py-3">
            <AlertCircle className="size-4 shrink-0 text-destructive" />
            <span className="text-[13px] text-destructive">{serverError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="flex w-full flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email" className="text-[12.5px] font-medium text-muted-foreground">
              Робочий email
            </Label>
            <Input
              id="email"
              type="text"
              placeholder="ім'я.прізвище@hirelume.dev"
              className="h-auto rounded-[10px] px-[15px] py-3 text-[14.5px]"
              {...register('email')}
            />
            {errors.email && (
              <span className="text-xs text-destructive">{errors.email.message}</span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password" className="text-[12.5px] font-medium text-muted-foreground">
              Пароль
            </Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••••"
              className="h-auto rounded-[10px] px-[15px] py-3 text-[14.5px]"
              {...register('password')}
            />
            {errors.password && (
              <span className="text-xs text-destructive">{errors.password.message}</span>
            )}
          </div>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 h-auto rounded-[10px] py-3.5 text-[14.5px] font-semibold"
          >
            {isSubmitting ? 'Вхід...' : 'Увійти'}
          </Button>
        </form>

        <p className="mt-7 text-center text-xs leading-relaxed text-muted-foreground">
          Проблеми з доступом — звертайтесь до системного адміністратора.
        </p>
      </div>
    </div>
  )
}
